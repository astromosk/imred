#!/usr/bin/env python
"""
rebin_fits.py

Re-bin a FITS image by an integer factor along each axis, using standard
astropy I/O and numpy array reshaping (no external re-binning dependency
beyond astropy + numpy).

Written with Claude AI prompt, 2026-09-08:
Produce a simple, but well documented, python script to re-bin fits images using standard astropy routines. Input parameters should include the bin factor (default 2x2) and the method for binning (sum, average, median, default=sum). Extra rows or columns that are remaining (e.g. an image with an odd number of rows would have one extra row that can not be combined with another in 2x2 binning) should be removed from the final image. Allow for multiple input files. By default rename the output files with a "_<bin_x>x<bin_y>" suffix. For example image1.fits would become image1_2x2.fits.
Additional refinements implemented to provide cross-platform (primarily Windows) support.

Binning method
--------------
For a bin factor of N x M (rows x columns), each output pixel is computed
from the corresponding N x M block of input pixels using one of:
    sum      - total flux in the block (default; preserves total counts,
               the standard choice for e.g. CCD/point-source photometry
               images where you want to conserve integrated flux)
    average  - mean of the block (preserves surface brightness / mean
               pixel value)
    median   - median of the block (robust to outliers/cosmic rays,
               but does not conserve flux)

Trimming
--------
If the image dimensions are not evenly divisible by the bin factor, the
"leftover" rows and/or columns (which cannot form a complete bin block)
are trimmed from the high-index (bottom/right) edge of the array before
binning. E.g. a 2x2 bin of a 2001-row image discards the last row before
binning, since only 2000 rows can be grouped into complete pairs.

Usage
-----
    python rebin_fits.py input.fits
    python rebin_fits.py input.fits --bin 2 --method sum
    python rebin_fits.py image1.fits image2.fits image3.fits --bin 2
    python rebin_fits.py input.fits --binx 2 --biny 3 --method average --outfile custom.fits

If --bin is given it sets both axes; --binx/--biny override it individually.

Multiple input files may be given. By default each output file is named
after its input with a "_<bin_x>x<bin_y>" suffix inserted before the
extension, e.g. "image1.fits" -> "image1_2x2.fits". --outfile overrides
this, and only works with a single input file. --outdir sends the
(auto-named) outputs to a different directory instead of alongside the
inputs.

Wildcards
---------
On Unix shells (bash/zsh), "*.fits" is expanded by the shell before Python
sees it, so it works without any special handling. On Windows (cmd.exe /
PowerShell), wildcards are NOT expanded by the shell, so this script also
expands any argument containing '*', '?', or '[' itself via glob, making
wildcard patterns work the same way on all platforms:
    python rebin_fits.py "*.fits" --bin 2
"""

import argparse
import glob
import os
import sys

import numpy as np
from astropy.io import fits


def trim_to_multiple(data: np.ndarray, bin_y: int, bin_x: int) -> np.ndarray:
    """
    Trim trailing rows/columns so each axis length is an exact multiple of
    its bin factor. Rows are trimmed from the bottom, columns from the
    right (i.e. the lowest-index pixels/rows are kept).

    Parameters
    ----------
    data : 2D ndarray
        Input image data (rows, cols).
    bin_y, bin_x : int
        Bin factors along the row (y) and column (x) axes.

    Returns
    -------
    2D ndarray
        Possibly-cropped view of the input array.
    """
    ny, nx = data.shape
    ny_trim = (ny // bin_y) * bin_y
    nx_trim = (nx // bin_x) * bin_x

    if ny_trim != ny or nx_trim != nx:
        print(
            f"Trimming image from ({ny}, {nx}) to ({ny_trim}, {nx_trim}) "
            f"to fit an integer number of {bin_y}x{bin_x} bins.",
            file=sys.stderr,
        )

    return data[:ny_trim, :nx_trim]


def rebin(data: np.ndarray, bin_y: int, bin_x: int, method: str = "sum") -> np.ndarray:
    """
    Re-bin a 2D array by (bin_y, bin_x), combining each block of pixels
    with the requested method.

    Parameters
    ----------
    data : 2D ndarray
        Input image data (rows, cols). Must already have dimensions that
        are exact multiples of bin_y/bin_x (use trim_to_multiple first).
    bin_y, bin_x : int
        Number of input rows/columns to combine into one output pixel.
    method : {'sum', 'average', 'median'}
        Combination method applied to each bin block.

    Returns
    -------
    2D ndarray
        The re-binned image, with shape (ny // bin_y, nx // bin_x).
    """
    ny, nx = data.shape
    new_ny, new_nx = ny // bin_y, nx // bin_x

    # Reshape so that each bin block becomes its own pair of axes:
    # (new_ny, bin_y, new_nx, bin_x), then reduce over the bin_y/bin_x axes.
    reshaped = data.reshape(new_ny, bin_y, new_nx, bin_x)

    if method == "sum":
        return reshaped.sum(axis=(1, 3))
    elif method == "average":
        return reshaped.mean(axis=(1, 3))
    elif method == "median":
        # Median needs the two block axes flattened into one before reducing.
        return np.median(
            reshaped.transpose(0, 2, 1, 3).reshape(new_ny, new_nx, -1), axis=2
        )
    else:
        raise ValueError(f"Unknown method '{method}'. Choose sum, average, or median.")


def rebin_fits_file(
    infile: str,
    outfile: str,
    bin_y: int = 2,
    bin_x: int = 2,
    method: str = "sum",
    ext: int = 0,
    overwrite: bool = True,
) -> None:
    """
    Read a FITS file, re-bin the requested image extension, update the WCS
    keywords for the new pixel scale, and write the result to a new file.

    Parameters
    ----------
    infile, outfile : str
        Paths to the input and output FITS files.
    bin_y, bin_x : int
        Bin factors along the row (y/NAXIS2) and column (x/NAXIS1) axes.
    method : {'sum', 'average', 'median'}
        Combination method (see `rebin`).
    ext : int
        FITS extension (HDU index) containing the image data.
    overwrite : bool
        Whether to overwrite `outfile` if it already exists.
    """
    with fits.open(infile) as hdul:
        hdu = hdul[ext]
        data = hdu.data
        header = hdu.header.copy()

        if data is None:
            raise ValueError(f"HDU {ext} in '{infile}' contains no image data.")
        if data.ndim != 2:
            raise ValueError(f"Expected a 2D image, got array with shape {data.shape}.")

        trimmed = trim_to_multiple(data, bin_y, bin_x)
        binned = rebin(trimmed, bin_y, bin_x, method=method)

        # Cast sums/averages of integer data back down sensibly; medians and
        # averages are inherently float, sums of float data stay float.
        if method == "sum" and np.issubdtype(data.dtype, np.integer):
            binned = binned.astype(data.dtype)

        # Update basic WCS/plate-scale keywords to reflect the new pixel size,
        # if present. Reference pixel (CRPIX) is rescaled to match; a full
        # WCS re-derivation (e.g. via astropy.wcs) is recommended for
        # science-grade astrometry beyond simple linear scaling.
        for key, factor in (("CDELT1", bin_x), ("CDELT2", bin_y)):
            if key in header:
                header[key] = header[key] * factor
        for key, factor in (
            ("CD1_1", bin_x), ("CD1_2", bin_x),
            ("CD2_1", bin_y), ("CD2_2", bin_y),
        ):
            if key in header:
                header[key] = header[key] * factor
        for key, factor in (("CRPIX1", bin_x), ("CRPIX2", bin_y)):
            if key in header:
                header[key] = (header[key] - 0.5) / factor + 0.5

        header["BINX"] = (bin_x, "Binning factor applied along NAXIS1 (x)")
        header["BINY"] = (bin_y, "Binning factor applied along NAXIS2 (y)")
        header["BINMETH"] = (method, "Binning combination method")
        header.add_history(
            f"Rebinned {bin_y}x{bin_x} using method='{method}' via rebin_fits.py"
        )

        fits.PrimaryHDU(data=binned, header=header).writeto(outfile, overwrite=overwrite)

    print(f"Wrote re-binned image ({binned.shape[0]}x{binned.shape[1]}) to '{outfile}'.")


def default_output_name(infile: str, bin_x: int, bin_y: int, outdir: str = None) -> str:
    """
    Build the default output filename by inserting a "_<bin_x>x<bin_y>"
    suffix before the file extension, e.g. "image1.fits" -> "image1_2x2.fits".

    Parameters
    ----------
    infile : str
        Path to the input FITS file.
    bin_x, bin_y : int
        Bin factors along x and y, used to build the suffix.
    outdir : str, optional
        If given, the output path is placed in this directory instead of
        alongside the input file.

    Returns
    -------
    str
        The generated output file path.
    """
    directory, filename = os.path.split(infile)
    stem, ext = os.path.splitext(filename)
    new_filename = f"{stem}_{bin_x}x{bin_y}{ext}"
    return os.path.join(outdir if outdir is not None else directory, new_filename)


def expand_infiles(patterns) -> list:
    """
    Expand a list of file paths/glob patterns into a flat, de-duplicated
    list of files, preserving first-seen order.

    Unix shells already expand wildcards (e.g. "*.fits") before argparse
    sees them, so each entry is typically a literal filename by the time
    it gets here. On shells that do NOT expand wildcards (Windows cmd.exe,
    PowerShell), an entry like "*.fits" arrives as a literal string; any
    such entry (containing '*', '?', or '[') is run through glob() here so
    behavior is consistent across platforms. Entries that don't look like
    a pattern are passed through as-is, even if they don't exist yet, so
    the usual "file not found" error still surfaces naturally later.

    Parameters
    ----------
    patterns : list of str
        Raw arguments as received from argparse (files and/or patterns).

    Returns
    -------
    list of str
        Expanded, de-duplicated file paths in first-seen order.

    Raises
    ------
    ValueError
        If a wildcard pattern matches no files.
    """
    seen = set()
    expanded = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            matches = sorted(glob.glob(pattern))
            if not matches:
                raise ValueError(f"Pattern '{pattern}' matched no files.")
        else:
            matches = [pattern]

        for match in matches:
            if match not in seen:
                seen.add(match)
                expanded.append(match)

    return expanded


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Re-bin one or more FITS images using astropy, with choice of sum/average/median combination."
    )
    parser.add_argument("infiles", nargs="+", help="Path(s) to input FITS file(s).")
    parser.add_argument(
        "--outfile", default=None,
        help="Path to write the re-binned FITS file. Only valid with a single input file; "
             "by default output files are auto-named as '<name>_<bin_x>x<bin_y>.fits'.",
    )
    parser.add_argument(
        "--outdir", default=None,
        help="Directory for auto-named output files (default: alongside each input file). "
             "Ignored if --outfile is given.",
    )
    parser.add_argument(
        "--bin", type=int, default=2,
        help="Bin factor for both axes (default: 2). Overridden by --binx/--biny.",
    )
    parser.add_argument("--binx", type=int, default=None, help="Bin factor along x (columns).")
    parser.add_argument("--biny", type=int, default=None, help="Bin factor along y (rows).")
    parser.add_argument(
        "--method", choices=["sum", "average", "median"], default="sum",
        help="Combination method for each bin block (default: sum).",
    )
    parser.add_argument(
        "--ext", type=int, default=0, help="FITS extension/HDU index containing the image (default: 0)."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    bin_x = args.binx if args.binx is not None else args.bin
    bin_y = args.biny if args.biny is not None else args.bin

    if bin_x < 1 or bin_y < 1:
        raise ValueError("Bin factors must be positive integers.")

    infiles = expand_infiles(args.infiles)

    if args.outfile is not None and len(infiles) > 1:
        raise ValueError("--outfile can only be used with a single input file; use --outdir instead.")

    for infile in infiles:
        outfile = args.outfile or default_output_name(infile, bin_x, bin_y, outdir=args.outdir)
        rebin_fits_file(
            infile, outfile,
            bin_y=bin_y, bin_x=bin_x,
            method=args.method, ext=args.ext,
        )


if __name__ == "__main__":
    main()
