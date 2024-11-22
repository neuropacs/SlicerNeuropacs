import logging
import os
import json

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


import qt
import ctk

# neuropacs module
neuropacs = None

#
# NeuropacsScriptedModule
#


class NeuropacsScriptedModule(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Parkinsonism Differentiation")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Diffusion")]
        self.parent.dependencies = []
        self.parent.contributors = ["Kerrick Cavanaugh (neuropacs Corp.)"]
        self.parent.helpText = _("""
neuropacs scripted loadable module bundled in an extension.
See more information at <a href="https://neuropacs.com">neuropacs documentation</a>.
""")
        self.parent.acknowledgementText = _("""
This file was originally developed by Kerrick Cavanaugh (neuropacs Corp.).
""")


#
# NeuropacsScriptedModuleWidget
#


# Config file selection
# 1. Default populated
# 2. Can select another config file or manually change the path
# ON VALIDATION PRESS -->
# 3. If selected another config file, should be populated with TEST subject and saved
# 4. If custom path, created (if possible), then TEST subject popualted and saved
# 5. If default, create if does not exist, and popualte with TEST subject and saved



class NeuropacsScriptedModuleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self.neuropacsOrderMap = {}
        self.neuropacsConfigPath = ""

        default_path = slicer.util.settingsValue("neuropacs/configPath", default = None)
        if  default_path == None:
            default_path = os.path.join(qt.QStandardPaths.writableLocation(qt.QStandardPaths.DocumentsLocation), "slicer_neuropacs.config")
            qt.QSettings().setValue("neuropacs/configPath", default_path)

        self.neuropacsConfigPath = default_path
        #     # self.load_npcs_file_selector(qt.QStandardPaths.writableLocation(qt.QStandardPaths.DocumentsLocation) + "/slicer_neuropacs.config")
        # else:
        #     self.load_npcs_file_selector(last_used_path)
        #     self.neuropacsConfigPath = last_used_path
        self.load_npcs_file_selector(default_path)


    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)


        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/NeuropacsScriptedModule.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        self.__setNeuropacsImage()

        # Buttons
        self.ui.neuropacsButton.connect("clicked(bool)", self.onNeuropacsButton)
        self.ui.refreshButton.connect("clicked(bool)", self.onRefreshButton)
        self.ui.validateKeyButton.connect("clicked(bool)", self.onValidateKeyButton)
        self.ui.helpButton.connect("clicked(bool)", self.onHelpButton)

        # Disable actions before API key validation
        self.__disableActions()

    def load_npcs_file_selector(self, default_path):
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        self.configPathFileSelector = ctk.ctkPathLineEdit()
        self.configPathFileSelector.filters = ctk.ctkPathLineEdit.Files
        self.configPathFileSelector.nameFilters = ['Config Files (*.config)', 'All Files (*)']
        self.configPathFileSelector.setCurrentPath(default_path)
        self.configPathFileSelector.settingKey = 'neuropacsConfigPath'

        # Add tooltip for guidance
        self.configPathFileSelector.toolTip = (
            "Select an existing config file or specify a new one to create."
        )

        # Connect the signal to handle the selected path
        self.configPathFileSelector.currentPathChanged.connect(self.on_config_path_changed)

        parametersFormLayout.addRow("Config file location:", self.configPathFileSelector)

    def on_config_path_changed(self, new_path):
        if not new_path:
            return
        self.neuropacsConfigPath = new_path  
        qt.QSettings().setValue("neuropacs/configPath", new_path)

    def create_config(self, path):
        default_config = {
            "TEST": "TEST",
        }
        try:
            self.neuropacsOrderMap = default_config
            with open(path, 'w') as config_file:
                json.dump(default_config, config_file)
        except Exception as e:
            slicer.util.errorDisplay(f"Failed to create configuration file '{path}': {str(e)}")
            raise e  # Re-raise the exception if necessary

    def configure_config(self, path):
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory '{directory}'.")
            except Exception as e:
                slicer.util.errorDisplay(f"Failed to create directory '{directory}': {str(e)}")
                return

        if not os.access(directory, os.W_OK):
            slicer.util.warningDisplay(f"No write permission in the directory '{directory}'.")
            return

        if os.path.isfile(path):
            # Load existing config
            try:
                if os.path.getsize(path) == 0:
                    self.create_config(path)
                else:
                    self.load_config(path)
                qt.QApplication.processEvents()
                print(f"Configuration file loaded from '{path}'.")
            except Exception as e:
                slicer.util.errorDisplay(f"Failed to load configuration: {str(e)}")
        else:
            # Create new config file
            try:
                self.create_config(path)
                print(f"Configuration file created at '{path}'.")
            except Exception as e:
                slicer.util.errorDisplay(f"Failed to create configuration file: {str(e)}")

    def setup_python_requirements(self):
        # install neuropacs pip module if not already installed
        global neuropacs
        try:
            self.ensure_latest_neuropacs_installed()
            import neuropacs
        except Exception as e:
            print(str(e))

    def ensure_latest_neuropacs_installed(self):
        import importlib.metadata
        import importlib.util
        import packaging.version
        import requests

        needToInstallNeuropacs = True
        installed_version = None
        latest_version = None

        # Check the installed version of neuropacs
        try:
            installed_version = importlib.metadata.version("neuropacs")
        except Exception:
            pass  # Neuropacs is not installed or there was an error getting the version

        # Get the latest version of neuropacs from PyPI
        try:
            response = requests.get("https://pypi.org/pypi/neuropacs/json")
            latest_version = response.json()["info"]["version"]
        except Exception:
            print("Error fetching the latest version of neuropacs from PyPI.")
            return

        # Compare versions and decide if we need to install/upgrade
        if installed_version is not None and packaging.version.parse(installed_version) >= packaging.version.parse(latest_version):
            # The installed version is up to date
            needToInstallNeuropacs = False

        if needToInstallNeuropacs:
            print(f"Upgrading neuropacs to version {latest_version}...")
            slicer.util.pip_install(f"neuropacs=={latest_version}")
        else:
            print(f"Neuropacs is already up to date (version {installed_version}).")

    def save_config(self):
        """Save the neuropacs order map to a JSON file."""
        with open(self.neuropacsConfigPath, 'w') as orderFile:
            json.dump(self.neuropacsOrderMap, orderFile)

    def load_config(self, path):
        """Load the neuropacs order map from a JSON file."""
        if os.path.exists(path):
            with open(path, 'r') as orderFile:
                self.neuropacsOrderMap = json.load(orderFile)
        else:
            with open(self.neuropacsConfigPath, "a") as file:
                json.dump({}, file)

    def storeNeuropacsOrder(self, patientId, orderId):
        """Associate an orderId with the patient."""
        self.neuropacsOrderMap[orderId] = patientId  # Store the order associated with the dataset
        self.save_config()  # Save the updated map to a file

    def getNeuropacsOrder(self, orderId):
        """Retrieve the neuropacs order associated with a patient."""
        return self.neuropacsOrderMap.get(orderId, "No order found")

    def _checkCanNeuropacs(self, caller=None, event=None) -> None:
        """Can neuropacs be pressed""" 
        if self._parameterNode:
            self.ui.neuropacsButton.toolTip = _("Run analysis")
            self.ui.neuropacsButton.enabled = True
        else:
            self.ui.neuropacsButton.toolTip = _("Enter API key and select Patient ID")
            self.ui.neuropacsButton.enabled = False

    def __downloadReport(self, orderId, format):
        """Download neuropacs biomarker report png"""
        with slicer.util.tryWithErrorDisplay(_("Failed to download report."), waitCursor=True):

            results = self.npcs.get_results(orderId, format)

            # Open file save dialog to let the user select where to save the image
            file_dialog = qt.QFileDialog()
            file_path = file_dialog.getSaveFileName(None, "Save Report", f"neuropacs_{orderId}.{format}")

            if file_path:
                if format == "txt" or format == "json" or format == "xml":
                    with open(file_path, "w") as report_file:
                        report_file.write(str(results))
                elif format == "png":
                    # Get results in png bytes
                    results_bytes = results.getvalue()
                    # Save the raw PNG image data to the selected file
                    with open(file_path, "wb") as report_file:
                        report_file.write(results_bytes)

            # Display the image/txt in a Slicer viewer
            if format == "png":
                self.display_png_in_slicer(file_path)
            elif format == "txt" or format == "json" or format == "xml":
                self.display_text_in_slicer(file_path)

            
            # Notify the user that the download is complete
            qt.QMessageBox.information(None, "Download Complete", f"Report neuropacs_{orderId}.{format} downloaded successfully at {file_path}")
        
    def display_png_in_slicer(self, file_path):
        # Load the PNG as a volume
        success, volume_node = slicer.util.loadVolume(file_path, returnNode=True)
        
        if success:
            # Set up the slice viewer to show the PNG image
            slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
            red_logic = slicer.app.layoutManager().sliceWidget("Red").sliceLogic()
            red_logic.GetSliceCompositeNode().SetBackgroundVolumeID(volume_node.GetID())
        else:
            print("Failed to load and display the PNG image.")

    def display_text_in_slicer(self, file_path):
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()

        # Create a new QTextEdit widget to display the content
        text_edit = qt.QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)  # Make the text read-only

        # Add the text widget to the Slicer layout
        main_window = slicer.util.mainWindow()
        central_widget = main_window.centralWidget()

        # Create a layout if not already present
        layout = central_widget.layout()
        if not layout:
            layout = qt.QVBoxLayout(central_widget)
            central_widget.setLayout(layout)

        # Add the QTextEdit to the main window's layout
        layout.addWidget(text_edit)

        # Optionally print a message confirming the text was displayed
        print("Text content loaded into Slicer's main window.")

    def __deleteOrder(self, order_id):
        """Delete an order from the table"""
        with slicer.util.tryWithErrorDisplay(_("Failed to delete order."), waitCursor=True):
            try:
                self.ui.infoLabel.setText(f"Deleting order {order_id}... ")
                qt.QApplication.processEvents()

                # Delete from neuropacs map
                if order_id in self.neuropacsOrderMap:
                    del self.neuropacsOrderMap[order_id]

                # Write new neuropacs map
                self.save_config()

                self.ui.infoLabel.setText(f"Order {order_id} deleted.")
                qt.QApplication.processEvents()

                # Re-render table
                self.populateOrderTable()

                self.ui.infoLabel.setText("")
                qt.QApplication.processEvents()
            except Exception as e:
                logging.error(f"Failed to delete order '{order_id}'")

    def __deleteExpiredOrders(self, expired_orders):
        """Delete expired orders after table population"""
        for exp in expired_orders:
            # Delete from neuropacs map
            if exp in self.neuropacsOrderMap:
                del self.neuropacsOrderMap[exp]

        # Write new neuropacs map
        self.save_config()

    
    def __extractInfoFromStatus(self, statusObj):
        return statusObj['info']

    def __extractProgressFromStatus(self, statusObj):
        return str(statusObj['progress']) + '%'

    def populateOrderTable(self):
        """Populate the TableView with existing orders"""
        self.ui.tableWidget.setRowCount(len(self.neuropacsOrderMap))
        self.ui.tableWidget.setColumnCount(6) # orderId, datasetId/patientId, info, progress, download report, delete
        self.ui.tableWidget.setHorizontalHeaderLabels(["Order ID", "Patient ID", "Info", "Progress", "Download Report", "Delete"])

        rowCount = 0
        exp_orders = []
        for order in self.neuropacsOrderMap:
            patientId = self.neuropacsOrderMap[order]

            # Get status params
            try:
                status = self.npcs.check_status(order)  
            except Exception as e:
                if ("Bucket not found") in str(e):
                    exp_orders.append(order)
                    continue

            status_info = self.__extractInfoFromStatus(status)
            status_progress = self.__extractProgressFromStatus(status)

            # Download button
            downloadButton = qt.QPushButton("Download")

            # Set button disabled if job is not done (100%)
            if not status_progress == "100%":
                downloadButton.setEnabled(False)

            # Create a QMenu to hold the download options
            downloadMenu = qt.QMenu(downloadButton)

            # Add the options to the menu
            downloadMenu.addAction("PNG", lambda _, order=order: self.__downloadReport(order, "png"))
            downloadMenu.addAction("TXT", lambda _, order=order: self.__downloadReport(order, "txt"))
            downloadMenu.addAction("JSON", lambda _, order=order: self.__downloadReport(order, "json"))
            downloadMenu.addAction("XML", lambda _, order=order: self.__downloadReport(order, "xml"))

            # Attach the menu to the download button
            downloadButton.setMenu(downloadMenu)


            # Populate table contents
            dataset_text = qt.QTableWidgetItem(patientId)
            order_id_text = qt.QTableWidgetItem(order)
            status_info_text = qt.QTableWidgetItem(status_info)
            status_progress_text = qt.QTableWidgetItem(status_progress)
            
            deleteButton = qt.QPushButton("Delete")
            deleteButton.clicked.connect(lambda _, order=order: self.__deleteOrder(order))

            self.ui.tableWidget.setItem(rowCount, 0, order_id_text)
            self.ui.tableWidget.setItem(rowCount, 1, dataset_text)
            self.ui.tableWidget.setItem(rowCount, 2, status_info_text)
            self.ui.tableWidget.setItem(rowCount, 3, status_progress_text)
            self.ui.tableWidget.setCellWidget(rowCount, 4, downloadButton)
            self.ui.tableWidget.setCellWidget(rowCount, 5, deleteButton)

            rowCount+=1

        # Delete found expired orders
        self.__deleteExpiredOrders(exp_orders)

    def populateDatasetDropdown(self):
        """Populate the ComboBox with available datasets (series in the DICOM database)."""
        dicomDatabase = slicer.dicomDatabase

        # Clear existing items in the dropdown
        self.ui.datasetComboBox.clear()

        # Get all patient UIDs
        patientUIDs = dicomDatabase.patients()
        for patientUID in patientUIDs:
            # Get the patient's name
            patientName = dicomDatabase.nameForPatient(patientUID)

            # Get studies for the patient
            studies = dicomDatabase.studiesForPatient(patientUID)
            for study in studies:
                # Get series for the study
                series = dicomDatabase.seriesForStudy(study)

                first_series = series[0]

                files = dicomDatabase.filesForSeries(first_series)

                # Get the first file path and then get the directory
                first_file_path = files[0]
                
                # Get the dataset folder (assumes that the dataset is one level above the DICOM files)
                dataset_folder = os.path.dirname(first_file_path)

                # Add the dataset name and file path to the dropdown
                self.ui.datasetComboBox.addItem(patientName, dataset_folder)

    def onHelpButton(self) -> None:
        """Help button"""
        with slicer.util.tryWithErrorDisplay(_("Failed to refresh neuropacs module."), waitCursor=True):
            self.openPDF()

    def onRefreshButton(self) -> None:
        """Refresh module"""
        with slicer.util.tryWithErrorDisplay(_("Failed to refresh neuropacs module."), waitCursor=True):
            self.ui.infoLabel.setText("Refreshing... ")
            qt.QApplication.processEvents()

            self.populateDatasetDropdown()
            self.populateOrderTable()

            self.ui.infoLabel.setText("")
            qt.QApplication.processEvents()
            logging.info("neuropacs module refreshed")

    def onValidateKeyButton(self) -> None:
        """Validate API key on button press"""
        global neuropacs
        with slicer.util.tryWithErrorDisplay(_("Failed to validate API key."), waitCursor=True):
            enteredKey = self.ui.apiKeyLineEdit.text
            # Initialize neuropacs
            try:
                self.configure_config(self.neuropacsConfigPath)

                self.ui.infoLabel.setText("Setting up Python requirements... ")
                qt.QApplication.processEvents()
                # Setup python requirements
                self.setup_python_requirements()

                self.ui.infoLabel.setText("Validating API key... ")
                qt.QApplication.processEvents()

                # initialize neuropacs
                self.npcs = neuropacs.init("https://jdfkdttvlf.execute-api.us-east-1.amazonaws.com/prod", enteredKey, "Slicer")
                self.npcs.connect()

                self.ui.infoLabel.setText("API key validated, populating... ")
                qt.QApplication.processEvents()

                # # Load the neuropacs order map from the file
                # self.load_config()

                # Populate the dropdown with available datasets
                self.populateDatasetDropdown()

                # Populate the table with existing orders
                self.populateOrderTable()

                # Enable user to run jobs
                self.__enableActions()

                self.ui.infoLabel.setText("")
                qt.QApplication.processEvents()

                logging.info("API key validated")
            except Exception as e:
                print(str(e))
                self.ui.infoLabel.setText("API key validation failed.")
                qt.QApplication.processEvents()
                logging.error("API key validation failed")

    def openPDF(self):
        """Open the PDF file in the system's default viewer."""
        # Path to the PDF file (make sure this path is correct)
        modulePath = os.path.dirname(slicer.util.modulePath(self.__module__))
        pdfPath = os.path.join(modulePath, 'Resources', 'Docs', 'neuropacs_instructions.pdf')

        # Check if the PDF file exists
        if os.path.exists(pdfPath):
            # Open the PDF in the system's default viewer
            qt.QDesktopServices.openUrl(qt.QUrl.fromLocalFile(pdfPath))
        else:
            qt.QMessageBox.critical(None, "Error", f"PDF not found: {pdfPath}")
        
    def __disableActions(self):
            """Disable actions"""
            self.ui.datasetComboBox.setEnabled(False)
            self.ui.neuropacsButton.setEnabled(False)
            self.ui.refreshButton.setEnabled(False)

    def __enableActions(self):
            """Enabled actions"""
            self.ui.validateKeyButton.setEnabled(False)
            self.ui.apiKeyLineEdit.setEnabled(False)
            self.ui.datasetComboBox.setEnabled(True)
            self.ui.neuropacsButton.setEnabled(True)
            self.ui.refreshButton.setEnabled(True)

    def __setNeuropacsImage(self):
        # Path to the image in the Resources/Icons folder
        modulePath = os.path.dirname(slicer.util.modulePath(self.__module__))
        imagePath = os.path.join(modulePath, 'Resources', 'Icons', 'NeuropacsScriptedModule.png')

        # Load the image using QPixmap
        pixmap = qt.QPixmap(imagePath)

        # Set the image to the QLabel
        self.ui.imageLabel.setPixmap(pixmap)

    def onNeuropacsButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to run neuropacs analysis."), waitCursor=True):
            try:
            # Get the folder path associated with the selected item in the dropdown
                selectedFolderPath = self.ui.datasetComboBox.currentData
                selectedPatient = self.ui.datasetComboBox.currentText

                if not selectedFolderPath or not selectedPatient:
                    raise Exception("Invalid patient selection.")

                # If selected folder path exists, continue
                if selectedFolderPath:

                    self.ui.infoLabel.setText("Uploading... (this may take a few minutes)")
                    qt.QApplication.processEvents()

                    # Create a new neuropacs order               
                    orderId = self.npcs.new_job()
                    logging.info(f"neuropacs order '{orderId}' created")

                    # Upload dataset
                    self.npcs.upload_dataset_from_path(orderId, selectedFolderPath)
                    logging.info(f"dataset uploaded")

                    self.ui.infoLabel.setText("Running order...")
                    qt.QApplication.processEvents()

                    # Run neuropacs order
                    self.npcs.run_job(orderId, 'Atypical/MSAp/PSP-v1.0')
                    logging.info(f"order {orderId} started")

                    self.ui.infoLabel.setText(f"Order {orderId} started...")
                    qt.QApplication.processEvents()

                    # Store neuropacs order
                    self.storeNeuropacsOrder(selectedPatient, orderId)
                    logging.info(f"order {orderId} successfully saved")

                    # Reload table
                    self.populateOrderTable()

                    self.ui.infoLabel.setText(f"")
                    qt.QApplication.processEvents()

                else:
                    slicer.util.errorDisplay("No dataset selected.")
            except Exception as e:
                self.ui.infoLabel.setText("Failed to run analysis.")
                qt.QApplication.processEvents()
                logging.error("Failed to run neuropacs analysis: ", str(e))


#
# NeuropacsScriptedModuleTest
#

class NeuropacsScriptedModuleTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_NeuropacsScriptedModule1()

    def test_NeuropacsScriptedModule1(self):
        """Integration tests"""

        self.delayDisplay("Starting the test")

        self.delayDisplay("Test passed")
