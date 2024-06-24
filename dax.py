Retail On Boarding = 
CALCULATE(
    COUNTROWS(archivo),
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "RecordCreated",
    CONTAINSSTRING(archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note], "SRS")
)
