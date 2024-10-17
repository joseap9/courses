indexOf(outputs('Concat Body Text'), 'Assessment Status:')

trim(first(split(substring(outputs('Concat Body Text'), add(outputs('Find Assessment Status'), length('Assessment Status:')), 100), ' ')))

if(contains(outputs('Extract Assessment Status'), 'New'), 'New', if(contains(outputs('Extract Assessment Status'), 'Pending Information/Remediation'), 'Pending Information/Remediation', if(contains(outputs('Extract Assessment Status'), 'Complete'), 'Complete', 'Unknown')))

addDays(triggerOutputs()?['body/receiveDateTime'], if(equals(coalesce(outputs('Date_Code_SLA'), 0), 20), 20, if(equals(coalesce(outputs('Date_Code_SLA'), 0), 15), 15, 5)))

addDays(triggerOutputs()?['body/receiveDateTime'], if(equals(outputs('Date_Code_SLA'), '20'), 20, if(equals(outputs('Date_Code_SLA'), '15'), 15, 5)))

if(
    or(
        equals(outputs('IOGloblalAssesmentStatus_Value'), 'New'),
        equals(outputs('ChileApprovalStatus_Value'), 'New')
    ), 
    'New', 
    if(
        or(
            equals(outputs('IOGloblalAssesmentStatus_Value'), 'Pending IO DPO Review'),
            equals(outputs('ChileApprovalStatus_Value'), 'Pending IO DPO Review')
        ), 
        'Pending IO DPO Review', 
        if(
            or(
                equals(outputs('IOGloblalAssesmentStatus_Value'), 'IO Review Complete'),
                equals(outputs('ChileApprovalStatus_Value'), 'IO Review Complete')
            ), 
            'IO Review Complete', 
            if(
                or(
                    equals(outputs('IOGloblalAssesmentStatus_Value'), 'Withdrawn or Unapproved'),
                    equals(outputs('ChileApprovalStatus_Value'), 'Withdrawn or Unapproved')
                ), 
                'Withdrawn or Unapproved', 
                'Unknown'
            )
        )
    )
)


=IFERROR(VLOOKUP(A2, Sheet1!A:B, 2, 0), LOOKUP(2, 1/(Sheet1!A$1:A2<>""), Sheet1!B$1:B2))

