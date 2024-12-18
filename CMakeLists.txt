cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerNeuropacs)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://neuropacs.github.io/SlicerNeuropacs/")
set(EXTENSION_CATEGORY "Diffusion")
set(EXTENSION_CONTRIBUTORS "Kerrick Cavanaugh (neuropacs Corp.)")
set(EXTENSION_DESCRIPTION "The neuropacs™ system is a software application intended to receive and analyze diffusion MRI data from patients aged 40 years and older presenting with Parkinson’s disease (PD) symptoms. The neuropacs™ system provides a report to aid neuroradiologists and/or neurologists in identifying patients with Atypical Parkinsonism (i.e., multiple system atrophy Parkinsonian variant (MSAp), or progressive supranuclear palsy (PSP)). The results of the neuropacs™ system are intended to provide supplemental information in conjunction with a standard neurological assessment and other clinical tests. Patient management decisions should not be made solely on the basis of analysis by the neuropacs™ system.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/neuropacs/SlicerNeuropacs/refs/heads/main/NeuropacsSlicerExtension.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/neuropacs/SlicerNeuropacs/refs/heads/main/NeuropacsScriptedModule/Resources/Examples/neuropacsModuleExample.png")
set(EXTENSION_DEPENDS "NA")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(NeuropacsScriptedModule)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
