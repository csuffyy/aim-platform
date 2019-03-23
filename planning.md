• Plan Image Search + Reports
    - Anna Update
    - Macgowan Update
    - Miller Update
• Plan Stroke Lab - review goals, prep
• Plan NLP-Daria Lab
• Plan Chris Help
- Have a plan !Saturday!
• Wayne Lee + Liam Update
• Ask Wayne for GE ETA
• Gautham

# Tuesday Update
- Review NLP emails !Saturday!
- Ask Robb for code !Monday!


# Epics
## Image Search: Goldenberg (Whole Body MR, Cancer MR), Macgowan (Heart MR), Miller (Brain MR)
- Basic Search ✔
- Basic Infrastructure ✔
- Basic Security 🕗
- Ingest all dicoms 🕕
- Advanced Search 🕑
- Targeted de-id 🕑
- Collections 🕑

## Reports: Goldenberg (Cancer Surveillance), Daria (NLP)
- Ingest all radiology reports
- Reports de-id
- Select Index

<p style='color:red'>This is some red text.</p>
<font color="red">This is some text!</font>
These are <b style='color:red'>red words</b>.


## Search by Clinical
- Connect to RedCap

## Internal SickKids Access
- Broad de-id UT
- Broad de-id MR
- Advanced Security
- Advanced Infrastructure

# Image Search Milestones
## Basic Security
- Lets Encrypt HTTPS !Tuesday!
- Elastic Security Proxy
- Change TOKEN

## Advanced Security
- Software updates / Mitigate vulnerabilities
- Active Directory
- RBAC
- Auditing


## Targeted PHI
- Metadata de-id
- Specialized pixel de-id

## Broad PHI
- MR Pixel de-id
- UT Pixel de-id
- Remove requisitions

## Ingest all dicoms
- Find all dicoms !Saturday!
- Color images !Sunday!
- Search Speed: Max value byte length !Sunday!
    Fix color thumbnail for picture of 
      ○ Face http://172.20.4.83:8080/index.html?input=http://172.20.4.83:8000/src/disk1/Images/NASLibrary13/def_20120321/def_20120321/def_20120321/DEMO4/126559797.dcm-0TO0-771100.dcm
      ○ 3D spine http://172.20.4.83:8000/src/disk1/Images/NASLibrary13/2000/02/08/9999993CORDEA__ADRIAN/119783495.dcm-0TO0-771100.dcm
- 100 million loaded
- Find bottleneck in parallel jobs
- Set max bytes for a field to ignore large matrixces: 172.20.4.83:8000/src/disk1/Images/NASLibrary12/2011/09/06/2457192/113254338.dcm-0TO0-771100.dcm "VOILUTSequence":"[(0028, 3002) LUT Descriptor                      US: [16384, 0, 14]\n(0028, 3003) LUT Explanation                     LO: 'NORMAL'\n(0028, 3006) LUT Data                            US: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
- Search Speed: Remove uncommon fields

## Ingest all Reports
- 1h How to identify reports !Saturday!
- 2h Setup database, example insert !Saturday!
- 2h Locate ALL Reports !Monday!
- 1h Write test cases !Monday!
- Select Report Index


## Basic Infrastructure
- Tmuxinator Deamon
- More Environment Variables
  - Jenkinsfile:        dir('image-archive/environments/production/') { // TODO 'production' here should be a variable, branch name?
  - (chris) Instead of removing last line, check if each line contains a dcm
  - TODO VARIABLE FOR PATH: double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs
- OpenStack Servers
- Jenkins CI/CD

## Advanced Infrastructure
- Montioring
- Functional Tests
  - Jenkins test that checks whether DWV loads DCM
  - Jenkins test that checks whether ReactiveSearch displays search results
  - Jenkins test that checks whether ReactiveSearch displays thumbnails

## Collections
- Create Collection
- Download Collection

## Basic Search
- Dicom Web Viewer
- Reactive Search
- Search any text field
- Word cloud
- Filter by modality, body part, gender, aquisition date
- Bay parts, diplay all? Sort by count? Blacklist body parts that are more numbers and whitespace than characters
- Modalities, diplay all? Sort by count? Whitelist Modalities plus the most popular ones?

## Advanced Search
- Ask around for search queries
- Filter by age
    https://stackoverflow.com/questions/54852930/how-to-toggle-on-or-off-a-reactivesearch-component-with-a-checkbox
- Search by list of MRNs
- Search operators: exclude field, in field(s) less than, greater than, not equal to, any
- Choose field for word cloud
- More features: Multi-channel, Z, timepoint


