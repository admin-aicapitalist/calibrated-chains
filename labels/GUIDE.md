# Invoice chain labeling guide

You label scanned business documents from the RVL-CDIP archive (1980s-90s, US, mostly tobacco-industry
correspondence). Each document has two files in `data/label_set/`:

- `<doc>.png`: the original scan. **This is the primary source; read it.**
- `<doc>.txt`: Tesseract OCR of the scan. Often garbled; use it only as a helper.

The dataset says every document here is an invoice, but that label is noisy. Judge each one yourself.

## Fields (one JSON object per document)

| field | values | meaning |
|---|---|---|
| `doc_id` | e.g. `"test/1038"` | file stem with the first `_` turned back into `/` |
| `is_invoice` | true / false | A bill from a vendor requesting payment for goods or services: invoice number or date, bill-to/remit-to, charges or line items, amounts, total due, payment terms. **false** for: purchase orders, payment vouchers or check requests prepared by the buyer, contribution or donation requests, statements of account, budgets, receipts, letters that merely mention an invoice. |
| `invoice_type` | `"standard"`, `"proforma"`, `"credit_note"`, `"recurring"`, or `null` | Only when `is_invoice` is true, else `null`. standard = bill for goods or services already delivered. proforma = preliminary bill, quote, estimate, or advance billing before delivery. credit_note = credit memo reducing an amount owed. recurring = periodic charge: retainer, subscription, rent, monthly fees, dues. |
| `amount_consistent` | true / false | true only if a total amount is legible AND consistent with the listed charges or line items (the arithmetic adds up where you can check it, nothing implausible). false if there's no legible total, the total conflicts with the charges, or the amount is implausible. For non-invoices: false. |
| `total` | number or `null` | The total due in dollars if legible, else `null`. |
| `approve` | true / false | Apply this policy exactly. Approve only if ALL hold: (1) it is an invoice requesting payment, not a statement, receipt, copy for records, or already-paid notice; (2) invoice_type is standard or recurring; (3) the vendor is identifiable; (4) the total due is legible and **under $5,000**; (5) remit-to or payment details (address to send payment, account, or payment terms with a payee) are present. Otherwise false. |
| `confidence` | `"high"`, `"medium"`, `"low"` | Your confidence in the labels as a whole (low if the scan is barely readable). |
| `note` | short string | One line of evidence, e.g. `"Invoice #4411, legal services, total $1,250.00, remit to address"`. Don't copy personal names of private individuals into notes. |

## Rules

- Read the image for every document. Don't label from the OCR text alone.
- Label what the document shows, not what the dataset says.
- Be consistent: when unsure between two invoice types, pick the more conservative one for approval
  (proforma over standard) and lower your `confidence`.
- Output exactly one JSON object per line (JSONL), no extra text, in the order given.
