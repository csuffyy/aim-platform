# Project Planning - AIM@SK Image Archive

Icon | Meaning
--- | ---
✔ | Work Complete
🕒 | Work Started
🕕 | Work Half Done
🕘 | Work Almost Done
![](https://img.shields.io/badge/-Monday-green.svg) | Task Scheduled for Day
![](https://img.shields.io/badge/Days-1-ff64b9.svg) | Remaining Effort for Task
![](https://img.shields.io/badge/Lab-Goldenberg-Blue.svg) | Associated Lab
![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) | Major Functional Milestone

<br>

## Priorities

#### 1.
##### Image Search Website ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

#### 2.

Prioritize according to revenue:

##### Macgowan Lab: Neonatal Cardiac MR Images ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)
##### Miller Lab: Pediatric Brian MR Images ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)
##### Goldenberg Lab: Cancer Surveillance ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
##### Doria Lab: NLP on Radiology Text Reports ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
##### Stroke Lab: Imaging Research Study  ![](https://img.shields.io/badge/Weeks-8-ff64b9.svg) ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-3_❔-ff64b9.svg)

#### 3.
##### Internal SickKids Access ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-6-ff64b9.svg)



## Stroke Lab: Imaging Research Study  ![](https://img.shields.io/badge/Weeks-8-ff64b9.svg)

The goal is to organize the Stroke Lab's DICOM images and make them more accessible. Data is coming from (a) prospective imaging studies (research study), (b) clinical images from SickKids, (c) also receiving 52 clinical images from other sites, and (d) Carbon, tatooween, silk servers at SickKids.

Lab members: rochelle.albert@sickkids.ca, amanda.robertson@sickkids.ca

##### Project Milestones:

- Ingestion:
    - Ingest images from Carbon server ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
    - Ingest images from Tatooween server ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
    - Ingest images from Silk server ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
    - Ingest images from 52 other sites ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
    - Ingest from future SickKids clinical images ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- Infrastructure:
    - Project Specific Web Front-end ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
    - Performance Optimization ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
    - Basic Monitoring ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
    - Functional Tests ![](https://img.shields.io/badge/Days-0.5-ff64b9.svg)
    - Continuous Integration ![](https://img.shields.io/badge/Days-0.5-ff64b9.svg)
    - DICOM Static Web Server (not PACS) ![](https://img.shields.io/badge/Days-3-ff64b9.svg) ![](https://img.shields.io/badge/Cost-❔-ff0000.svg)
- Security:
    - De-id Image Sets ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
    - Authentication ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
    - Data Backup ![](https://img.shields.io/badge/Days-1-ff64b9.svg) ![](https://img.shields.io/badge/Cost-❔-ff0000.svg)
    - Master Linking List ![](https://img.shields.io/badge/Days-1-ff64b9.svg)

##### Advanced Milestones:

- Search Images by Clinical Data in RedCap ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-3_❔-ff64b9.svg)

##### Prerequisite Milestones:

- Image Search Website ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

## Goldenberg Lab: Cancer Surveillance ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

Anna has 4 summer students who need (a) all available whole body MR images, and (b) all available MR images of cancer. They also want to use the radiology text reports to inform prediction.

Lab Members: nyulik@gmail.com, eman.marie@sickkids.ca

##### Project Milestones:

- Find images of interest ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- De-id image sets ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- Data quality improvements ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Master linking list ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Security improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Infrastucture improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Other project specific needs ![](https://img.shields.io/badge/Days-3-ff64b9.svg)

##### Prerequisite Milestones:

- Image Search Website ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)
- Radiology Reports Search ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)

## Miller Lab: Pediatric Brian MR Images ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

Looking to develop multi-modal quantitative imaging of brain development, analysis over time with 8 year outcomes. Also seeking normative dataset of age 7.5-9.5 brain scans. Looking for image modalities: (a) Volumetric T1 (MPGR or SPGR; 1mm3 resolution), (b) Volumetric T2 (usually 2mm3 resolution), (c) Diffusion tensor imaging (as opposed to diffusion weighted imaging), and (d) MR Spectroscopy.

Lab Members: steven.miller@sickkids.ca, jessie.guo@sickkids.ca

##### Project Milestones:

- Find images of interest ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- De-id image sets ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- Data quality improvements ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Master linking list ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Security improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Infrastucture improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Other project specific needs ![](https://img.shields.io/badge/Days-3-ff64b9.svg)

##### Prerequisite Milestones:

- Image Search Website ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

## Macgowan Lab: Neonatal Cardiac MR Images ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

Looking for neonatal cardiac MR images.

Lab Members: christopher.macgowan@sickkids.ca, cthuynh91@gmail.com

##### Project Milestones:

- Find images of interest ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- De-id image sets ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- Data quality improvements ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Master linking list ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Security improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Infrastucture improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Other project specific needs ![](https://img.shields.io/badge/Days-3-ff64b9.svg)

##### Prerequisite Milestones:

- Image Search Website ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

## Doria Lab: NLP on Radiology Text Reports ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

Looking to do NLP on radiology text reports.

Lab Members: zitian.zhang@sickkids.ca, afsaneh.amirabadi@sickkids.ca, hojjat.salehinejad@sickkids.ca

##### Project Milestones:

- Radiology Reports Search ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
- Data quality improvements ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Master linking list ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Security improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Infrastucture improvements ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Other project specific needs ![](https://img.shields.io/badge/Days-3-ff64b9.svg)

##### Prerequisite Milestones:

- Image Search Website ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)

## Care4Rare: Unknown

Details unknown. Marta mentioned they need an imaging database need in relation to the Care4Rare collaboration.

<br>

## Major Functional Milestones
### Image Search Website ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-3-ff64b9.svg)
![](https://img.shields.io/badge/Lab-Goldenberg-Blue.svg) ![](https://img.shields.io/badge/Lab-Macgowan-Blue.svg) ![](https://img.shields.io/badge/Lab-Miller-Blue.svg) ![](https://img.shields.io/badge/Lab-Stroke-Blue.svg) ![](https://img.shields.io/badge/Lab-Doria-Blue.svg)

Web search tool to find and download images. All other milestones must follow in no particular order.

Subtasks:

- ✔ Basic Search
- ✔ Basic Infrastructure
- 🕗 Basic Security ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- 🕕 Ingest all dicoms ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- 🕑 Advanced Search ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- 🕑 Collections ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)

### Radiology Reports Search ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
![](https://img.shields.io/badge/Lab-Goldenberg-Blue.svg) ![](https://img.shields.io/badge/Lab-Doria-Blue.svg) 

### Search by Clinical Data ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-3_❔-ff64b9.svg)
![](https://img.shields.io/badge/Lab-Stroke-Blue.svg)

### Internal SickKids Access ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-6-ff64b9.svg)

- De-id All UT Images ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- De-id All MR Images ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)
- Advanced Security ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)
- Advanced Infrastructure ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)




<br>

## Implementation Milestones
### Basic Security  ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Days-1-ff64b9.svg)

- ✔ Authentication Web Page ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ Static Webserver Authentication ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Lets Encrypt HTTPS ![](https://img.shields.io/badge/-Tuesday-green.svg) ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)
- 🕕 Elastic Security Proxy ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
- Change auth TOKEN ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)

### Advanced Security ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)

- Software updates ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- Active Directory ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- RBAC ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Auditing ![](https://img.shields.io/badge/Days-3-ff64b9.svg)

### Ingest All Dicoms ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
![](https://img.shields.io/badge/Lab-Goldenberg-Blue.svg) ![](https://img.shields.io/badge/Lab-Macgowan-Blue.svg) ![](https://img.shields.io/badge/Lab-Miller-Blue.svg) ![](https://img.shields.io/badge/Lab-Doria-Blue.svg)

- ✔ Ingestion Script `load_elastic.py` ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- ✔ HPF Script `aim-qsub.sh` ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- 🕕 Find all dicoms ![](https://img.shields.io/badge/-Saturday-green.svg) ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
- Fix Color Thumbnails ![](https://img.shields.io/badge/-Monday-green.svg) ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
- Search Speed: Max value byte length ![](https://img.shields.io/badge/-Monday-green.svg) ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
- Fix color thumbnail for picture of:
      - Face :8080/index.html?input=:8000/src/disk1/Images/NASLibrary13/def_20120321/def_20120321/def_20120321/DEMO4/126559797.dcm
      - 3D spine :8000/src/disk1/Images/NASLibrary13/2000/02/08/9999993CORDEA__ADRIAN/119783495.dcm
- 🕕 Ingest 100 million images ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Find bottleneck in parallel jobs ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Set max bytes for a field to ignore large matrixces ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
    - :8000/src/disk1/Images/NASLibrary12/2011/09/06/2457192/113254338.dcm "VOILUTSequence":"[(0028, 3002) LUT Descriptor                      US: [16384, 0, 14]\n(0028, 3003) LUT Explanation                     LO: 'NORMAL'\n(0028, 3006) LUT Data                            US: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
- Search Speed: Remove uncommon fields ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)

### De-Id All Dicoms ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2.5-ff64b9.svg)

- Metadata de-id ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- MR Pixel de-id ![](https://img.shields.io/badge/Days-5-ff64b9.svg)
- 🕕 UT Pixel de-id ![](https://img.shields.io/badge/Days-5-ff64b9.svg)
- Remove requisitions ![](https://img.shields.io/badge/Days-2-ff64b9.svg)

### Radiology Reports Search ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Lab-Goldenberg-Blue.svg) ![](https://img.shields.io/badge/Lab-Doria-Blue.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)

- Local all reports ![](https://img.shields.io/badge/-Saturday-green.svg) ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)
- Setup database, example insert ![](https://img.shields.io/badge/-Sunday-green.svg) ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)
- Parse Report Data Format ![](https://img.shields.io/badge/-Monday-green.svg) ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- Write test cases ![](https://img.shields.io/badge/-Monday-green.svg) ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
- De-Id Reports ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- Ingest Reports ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- Select Report Index ![](https://img.shields.io/badge/Days-2-ff64b9.svg)


### Basic Infrastructure ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Days-0.5-ff64b9.svg)

- ✔ HPC Tunnels ![](https://img.shields.io/badge/Hours-3-ff64b9.svg)
- ✔ ElasticSearch Database ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ OpenStack Servers ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ Enviornments: Local, Development, Production ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ Jenkins CI/CD ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- ✔ Tmuxinator Launch ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ Sample Images ![](https://img.shields.io/badge/Hours-3-ff64b9.svg)
- Tmuxinator Deamon ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
- More Environment Variables ![](https://img.shields.io/badge/Hours-3-ff64b9.svg)
    - Jenkinsfile:        dir('image-archive/environments/production/') { // To do: 'production' here should be a variable, branch name
    - (chris) Instead of removing last line, check if each line contains a dcm
    - Todo Variable For Path: double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs

### Advanced Infrastructure ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-2-ff64b9.svg)

- Montioring ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- Functional Tests ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
    - Check whether DWV loads DCM
    - Check whether ReactiveSearch displays search results
    - Check whether ReactiveSearch displays thumbnails
- Advanced DICOM Static Web Server ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Server Improvements ![](https://img.shields.io/badge/Days-2-ff64b9.svg)

### Collections ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)

- 🕑 Create Collection ![](https://img.shields.io/badge/Days-3-ff64b9.svg)
- Download Collection ![](https://img.shields.io/badge/Days-2-ff64b9.svg)

### Basic Search ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Done-success.svg)

- ✔ Dicom Web Viewer ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
- ✔ ReactiveSearch ![](https://img.shields.io/badge/Days-1-ff64b9.svg)
- ✔ Search any text field ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)
- ✔ Word cloud ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)
- ✔ Filter by modality, body part, gender, aquisition date ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)

### Advanced Search ![](https://img.shields.io/badge/Epic-Image_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Reports_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Clinical_Search-blueviolet.svg) ![](https://img.shields.io/badge/Epic-Internal_SickKids-blueviolet.svg) ![](https://img.shields.io/badge/Weeks-1-ff64b9.svg)

- Filter Options Cleanup ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
    - Display fewer body part filters. Sort by count. Blacklist body parts that are more numbers and whitespace than characters. 
    - Display fewer modalities filters. Sort by count. Whitelist Modalities plus the most popular ones.
- Gather search query requirements from labs ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
- Filter by age ![](https://img.shields.io/badge/Hours-4-ff64b9.svg)
    https://stackoverflow.com/questions/54852930/how-to-toggle-on-or-off-a-reactivesearch-component-with-a-checkbox
- Search by list of MRNs ![](https://img.shields.io/badge/Hours-2-ff64b9.svg)
- Search operators: exclude field, in field(s) less than, greater than, not equal to, any ![](https://img.shields.io/badge/Days-2-ff64b9.svg)
- Choose field for word cloud ![](https://img.shields.io/badge/Hours-1-ff64b9.svg)



<br>
<br>


# Misc To Do

- Review NLP emails ![](https://img.shields.io/badge/-Saturday-green.svg)
- Chris Help ![](https://img.shields.io/badge/-Monday-green.svg)
- Gautham Update ![](https://img.shields.io/badge/-Monday-green.svg)
- Robb Code and CHMOD ![](https://img.shields.io/badge/-Monday-green.svg)
- Anna Update ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Macgowan Update ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Miller Update ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Stroke Lab Update ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Doria Lab Update ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Ask Wayne for GE ETA, Report better format? ![](https://img.shields.io/badge/-Wednesday-green.svg)
- Wayne Lee + Liam Update ![](https://img.shields.io/badge/-Monday-green.svg)

##### Nice to Have

- More features for multi-series, multi-dimensional dicoms
