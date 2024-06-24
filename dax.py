Retail On Boarding = 
CALCULATE(
    COUNTROWS(archivo),
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "RecordCreated",
    CONTAINSSTRING(archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note], "SRS")
)

second note = 
LOOKUPVALUE(
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note], 
    archivo[ResultRecords.ResultRecord.Id.#text], archivo[ResultRecords.ResultRecord.Id.#text],
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action], "NewNote"
)