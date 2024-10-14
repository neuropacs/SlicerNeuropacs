# neuropacs™ Slicer Extension

The neuropacs™ system is a software application intended to receive and analyze
diffusion MRI data from patients aged 40 years and older presenting with Parkinson’s
disease (PD) symptoms. The neuropacs™ system provides a report to aid
neuroradiologists and/or neurologists in identifying patients with Atypical Parkinsonism
(i.e., multiple system atrophy Parkinsonian variant (MSAp), or progressive supranuclear
palsy (PSP)). The results of the neuropacs™ system are intended to provide
supplemental information in conjunction with a standard neurological assessment and
other clinical tests. Patient management decisions should not be made solely on the basis
of analysis by the neuropacs™ system.

<!-- ## Getting Started

These instructions will give you a copy of the project up and running on
your local machine for development and testing purposes. See deployment
for notes on deploying the project on a live system. -->

<!-- ### Prerequisites

Requirements for the software and other tools to build, test and push

- [Example 1](https://www.example.com)
- [Example 2](https://www.example.com) -->

## Getting Started

### Usage

1. Obtain an API key

2. Enter your API key and press "Validate"

This will validate your API key with the neuropacs™ servers and start a new session. If there are existing jobs, the table will also be populated.

3. Select a DICOM dataset from the dropdown list.

For instructions on how to upload a DICOM datasets, refer to Slicer 3D documentation.

4. Select "Run analysis" to begin the upload and analysis process.

5. Once started, your order will automatically appear in the table below.

6. Once your order is completed, the option to download will become availble in PNG, TXT, JSON, or XML format.

7. Refresh the DICOM dataset dropdown and table by selecting the "Refresh" button.

### Installing Locally

Step by step instructions on how to get a development environment running:

1. Clone the repository

   git clone https://github.com/neuropacman/SlicerNeuropacs

2. Navigate to Slicer 3D "Extension Manager"

3. Select "Select Extension"

4. Select the "SlicerNeuropacs" folder

5. Select "Okay" to add the extension

6. Restart Slicer 3D

The extension should now be available in the extention dropdowns under the "Diffusion" tab.
For usage instructions, refer to the "Usage" section of this readme.

## Authors

- **Kerrick Cavanaugh** - Lead Software Enginee, neuropacs Corp.

## License

This project is licensed under the [MIT](LICENSE.md)
