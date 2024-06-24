Retail On Boarding = 
CALCULATE(
    COUNTROWS(archivo),
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "RecordCreated",
    CONTAINSSTRING(archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note], "SRS")
)

second note = 
VAR currentId = archivo[ResultRecords.ResultRecord.Id.#text]
RETURN
CALCULATE(
    FIRSTNONBLANK(
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note], 
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note]
    ),
    archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "NewNote",
    FILTER(
        archivo,
        archivo[ResultRecords.ResultRecord.Id.#text] = currentId &&
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "RecordCreated"
    )
)
