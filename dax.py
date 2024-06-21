second note = 
VAR currentId = archivo[ResultRecords.ResultRecord.Id.#text]
RETURN
CALCULATE(
    FIRSTNONBLANK(
        SELECTCOLUMNS(
            FILTER(
                archivo, 
                archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Action] = "NewNote" &&
                archivo[ResultRecords.ResultRecord.Id.#text] = currentId
            ),
            "Note", archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note]
        ), 
        archivo[ResultRecords.ResultRecord.AuditRecords.AuditRecord.Note]
    )
)
