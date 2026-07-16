# resources

Place sample images here for manual testing with `apps/client.py`:

- `sample_document.jpg` — a raw phone photo of a document (used by `DocumentCrop`).
- `sample_cropped_document.jpg` — the flattened output of `DocumentCrop`, used as the
  `ScanEffect` input.
- `sample_reference_patch.jpg` — optional: a photo of a blank/white patch taken under
  the same lighting as the document, used as `ScanEffect`'s `inputReferenceImage` for
  white-balance correction in `ColorScan` mode.

These files are not committed to the repository; provide your own test images locally.
