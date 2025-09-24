let
  shipment = "0120",
  path = "out/" & shipment & "_Audit_Result.csv",
  Source = Csv.Document(File.Contents(path),[Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
  Promote = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in Promote