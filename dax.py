second note = 
VAR currentId = archivo[ResultRecords.ResultRecord.Id.#text]
RETURN
CALCULATE(
    FIRSTNONBLANK(
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note],
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "NewNote" &&
        archivo[ResultRecords.ResultRecord.Id.#text] = currentId
    )
)