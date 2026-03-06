require 'json'
require 'fileutils'

# Create the data/claims folder inside your project
FileUtils.mkdir_p('data/claims')

docs = [
  {claimId:'CLM-0001',memberId:'M-10001',provider:'Peachtree Clinic',serviceDate:'2025-12-18',submittedDate:'2025-12-20',status:'PAID',amountBilled:420.00,amountAllowed:310.00,amountPaid:295.00,diagnosisCodes:['J06.9'],procedureCodes:['99213'],facility:{state:'GA',city:'Atlanta'}},
  {claimId:'CLM-0002',memberId:'M-10002',provider:'Macon Imaging',serviceDate:'2026-01-05',submittedDate:'2026-01-07',status:'DENIED',denialReason:'Missing prior authorization',amountBilled:980.00,amountAllowed:0.00,amountPaid:0.00,diagnosisCodes:['M54.5'],procedureCodes:['72148'],facility:{state:'GA',city:'Macon'}},
  {claimId:'CLM-0003',memberId:'M-10001',provider:'Middle GA Ortho',serviceDate:'2026-01-12',submittedDate:'2026-01-14',status:'PENDING',amountBilled:1500.00,amountAllowed:0.00,amountPaid:0.00,diagnosisCodes:['S83.511A'],procedureCodes:['29888'],facility:{state:'GA',city:'Warner Robins'}},
  {claimId:'CLM-0004',memberId:'M-10003',provider:'Savannah Pediatrics',serviceDate:'2026-02-02',submittedDate:'2026-02-03',status:'PAID',amountBilled:210.00,amountAllowed:180.00,amountPaid:170.00,diagnosisCodes:['H66.90'],procedureCodes:['99214'],facility:{state:'GA',city:'Savannah'}},
  {claimId:'CLM-0005',memberId:'M-10004',provider:'Augusta ER',serviceDate:'2026-02-10',submittedDate:'2026-02-10',status:'DENIED',denialReason:'Coverage terminated',amountBilled:5200.00,amountAllowed:0.00,amountPaid:0.00,diagnosisCodes:['R07.9'],procedureCodes:['93010','99285'],facility:{state:'GA',city:'Augusta'}},
  {claimId:'CLM-0006',memberId:'M-10002',provider:'Athens Family Med',serviceDate:'2026-02-14',submittedDate:'2026-02-16',status:'PAID',amountBilled:160.00,amountAllowed:140.00,amountPaid:130.00,diagnosisCodes:['I10'],procedureCodes:['99213'],facility:{state:'GA',city:'Athens'}},
  {claimId:'CLM-0007',memberId:'M-10005',provider:'Columbus Lab Services',serviceDate:'2026-01-22',submittedDate:'2026-01-23',status:'PENDING',amountBilled:85.00,amountAllowed:0.00,amountPaid:0.00,diagnosisCodes:['E11.9'],procedureCodes:['83036'],facility:{state:'GA',city:'Columbus'}},
  {claimId:'CLM-0008',memberId:'M-10006',provider:'Valdosta Cardiology',serviceDate:'2025-11-30',submittedDate:'2025-12-02',status:'PAID',amountBilled:760.00,amountAllowed:640.00,amountPaid:615.00,diagnosisCodes:['I48.91'],procedureCodes:['93000'],facility:{state:'GA',city:'Valdosta'}},
  {claimId:'CLM-0009',memberId:'M-10003',provider:'Atlanta Neuro',serviceDate:'2026-02-20',submittedDate:'2026-02-22',status:'DENIED',denialReason:'Duplicate claim',amountBilled:2400.00,amountAllowed:0.00,amountPaid:0.00,diagnosisCodes:['G43.909'],procedureCodes:['70551'],facility:{state:'GA',city:'Atlanta'}},
  {claimId:'CLM-0010',memberId:'M-10001',provider:'Peachtree Clinic',serviceDate:'2026-02-25',submittedDate:'2026-02-26',status:'PAID',amountBilled:120.00,amountAllowed:100.00,amountPaid:95.00,diagnosisCodes:['Z00.00'],procedureCodes:['99395'],facility:{state:'GA',city:'Atlanta'}}
]

docs.each do |doc|
  filename = "data/claims/#{doc[:claimId].downcase}.json"
  File.write(filename, JSON.pretty_generate(doc))
  puts "Created #{filename}"
end

puts "Done! Created #{docs.length} claim files in data/claims/"
