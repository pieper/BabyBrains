import os
import unittest
import subprocess
import vtkITK
from __main__ import vtk, qt, ctk, slicer

#
# BabyBrowser
#

class BabyBrowser:
  def __init__(self, parent):
    parent.title = "Baby Browser"
    parent.categories = ["Work in Progress"]
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)"]
    parent.helpText = """
    This module helps organize and process collections of volumes
    """
    parent.acknowledgementText = """
    This file was originally developed by Steve Pieper, Isomics, Inc.  and was partially funded by NIH grants 1R01EB014947-013 and P41RR013218-12S1.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['BabyBrowser'] = self.runTest

  def runTest(self):
    tester = BabyBrowserTest()
    tester.runTest()

#
# qBabyBrowserWidget
#

class BabyBrowserWidget:
  def __init__(self, parent = None):
    self.logic = BabyBrowserLogic()
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "BabyBrowser Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Data Area
    #
    dataCollapsibleButton = ctk.ctkCollapsibleButton()
    dataCollapsibleButton.text = "Data"
    self.layout.addWidget(dataCollapsibleButton)
    dataFormLayout = qt.QFormLayout(dataCollapsibleButton)

    # pick the data directory and file pattern
    self.pathEdit = ctk.ctkPathLineEdit()
    self.pathEdit.setCurrentPath('/Users/pieper/data/babybrains/orig/')
    self.patternEdit = qt.QLineEdit()
    self.patternEdit.setText('mprage-%d.mgz')
    self.loadButton = qt.QPushButton()
    self.loadButton.text = "Load Data"
    self.dataSlider = ctk.ctkSliderWidget()
    self.dataSlider.setDecimals(0)
    self.dataSlider.enabled = False
    dataFormLayout.addRow("Data path: ", self.pathEdit)
    dataFormLayout.addRow("Data pattern: ", self.patternEdit)
    dataFormLayout.addRow(self.loadButton)
    dataFormLayout.addRow("Data Select", self.dataSlider)

    self.loadButton.connect('clicked()', self.onLoad)
    self.dataSlider.connect('valueChanged(double)', self.onDataSlider)


    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    parametersCollapsibleButton.collapsed = True
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.outputSelector.selectNodeUponCreation = False
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = False
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onLoad(self):
    """Load data with the current path and pattern.  Pattern should include %d.
    We load from 1 until the file does not exist"""
    self.logic.loadBabies(self.pathEdit.currentPath, self.patternEdit.text)
    self.dataSlider.enabled = len(self.logic.images) !=0
    self.dataSlider.maximum = len(self.logic.images) - 1

  def onDataSlider(self,value):
    self.logic.showBaby(int(value))


  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = BabyBrowserLogic()
    print("Run the algorithm")
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode())

  def onReload(self,moduleName="BabyBrowser"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

  def onReloadAndTest(self,moduleName="BabyBrowser"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# BabyBrowserLogic
#

class BabyBrowserLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.images = None
    self.rasToIJK = None

  def loadBabies(self,directoryPath,pattern,maxIndex=None):
    self.images = []
    filePaths = []
    index = 1
    import os.path
    while True:
      filePath = os.path.join(directoryPath, pattern % index)
      if not os.path.exists(filePath):
        break
      filePaths.append(filePath)
      index += 1
      if maxIndex and index > maxIndex:
        break

    if len(filePaths) == 0:
      return
      
    middleBabyPath = filePaths[len(filePaths)/2]
    babyVolume = self.babyVolume(middleBabyPath)

    #transtor = slicer.vtkMRMLTransformStorageNode()
    reader = reader = vtkITK.vtkITKArchetypeImageSeriesScalarReader()
    reader.SetSingleFile(1)
    reader.SetUseOrientationFromFile(1)
    #reader.SetDesiredCoordinateOrientationToAxial()
    reader.SetOutputScalarTypeToNative()
    reader.SetUseNativeOriginOn()
    changeInfo = vtk.vtkImageChangeInformation()
    changeInfo.SetInputConnection( reader.GetOutputPort() )
    changeInfo.SetOutputSpacing( 1, 1, 1 )
    changeInfo.SetOutputOrigin( 0, 0, 0 )
    self.images = {}
    self.rasToIJKs = {}
    #self.toTemplate = {}
    for filePath in filePaths:
      print("Loading %s" % filePath)
      reader.SetArchetype(filePath)
      changeInfo.Update()
      self.rasToIJKs[filePath] = vtk.vtkMatrix4x4()
      self.rasToIJKs[filePath].DeepCopy(reader.GetRasToIjkMatrix())
      self.images[filePath] = vtk.vtkImageData()
      self.images[filePath].DeepCopy(changeInfo.GetOutput())
      #t = template
      #transDir = self.babydir + '/xformsTo' + t[t.find('/')+1:t.find('.')]
      #id = file[file.rfind('/')+1:file.find('.')]
      #transtor.SetFileName(transDir + '/' + id + '.mat')
      #transtor.ReadData(self.transform)
      #self.toTemplate[file] = vtk.vtkMatrix4x4()
      #self.toTemplate[file].DeepCopy(self.transform.GetMatrixTransformToParent())

  def showBaby(self,index):
    """display the image for the given index.
    """
    if not self.images:
      return
    filePath = self.images.keys()[index]
    image = self.images[filePath]
    rasToIJK = self.rasToIJKs[filePath]
    #toTemplate = self.toTemplate[self.samples[sampleage][which]]
    self.babyVolume().SetRASToIJKMatrix(rasToIJK)
    self.babyVolume().SetAndObserveImageData(image)
    #self.transform.GetMatrixTransformToParent().DeepCopy(toTemplate)


  def babyVolume(self,filePath=None,name='baby'):
    """Make a volume node as the target for the babys"""

    babyVolume = slicer.util.getNode(name)
    # create the volume for displaying the baby 
    if not babyVolume:
      volumeLogic = slicer.modules.volumes.logic()
      babyVolume = volumeLogic.AddArchetypeScalarVolume (filePath, "baby", 0, None)
      displayNode = babyVolume.GetDisplayNode()
      displayNode.SetWindow(3000)
      displayNode.SetLevel(1700)

      # automatically select the volume to display
      mrmlLogic = slicer.app.applicationLogic()
      selNode = mrmlLogic.GetSelectionNode()
      selNode.SetReferenceActiveVolumeID(babyVolume.GetID())
      mrmlLogic.PropagateVolumeSelection()

      # Create transform node
      transform = slicer.vtkMRMLLinearTransformNode()
      transform.SetName('Baby to Template' )
      slicer.mrmlScene.AddNode(transform)
      babyVolume.SetAndObserveTransformNodeID(transform.GetID())
    return babyVolume

  def biasCorrect(self,filePathIn,filePathOut):
    args = [
      os.environ['SLICER_HOME']+"/lib/Slicer-4.2/cli-modules/N4ITKBiasFieldCorrection",
      "--inputimage " + filePathIn,
      "--outputimage " + filePathOut,
      "--meshresolution 1,1,1",
      "--splinedistance 0",
      "--bffwhm 0",
      "--iterations 500,400,300",
      "--convergencethreshold 0.0001",
      "--bsplineorder 3",
      "--shrinkfactor 4",
      "--wienerfilternoise 0",
      "--nhistogrambins 0",
      ]
    self.process = subprocess.Popen(args,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    line = self.process.stdout.readline()
    while line != '':
      print(line)
      line = self.process.stdout.readline()
      slicer.app.processEvents()

    self.process.wait()

  def biasCorrectAll(self):
    """Run the bias corrector on all loaded baby volumes"""
    for filePath in self.images.keys():
      print(filePath)
      fileName = os.path.basename(filePath)
      origDir = os.path.dirname(filePath)
      dataDir = os.path.dirname(origDir)
      correctedDir = os.path.join(dataDir,'corrected')
      if not os.path.exists(correctedDir):
        os.mkdir(correctedDir)
      correctedPath = os.path.join(correctedDir,fileName)
      print ('running: biasCorrect(%s,%s)' % (filePath,correctedPath))
      self.biasCorrect(filePath,correctedPath)






  def hasImageData(self,volumeNode):
    """This is a dummy logic method that 
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def run(self,inputVolume,outputVolume):
    """
    Run the actual algorithm
    """
    return True


class BabyBrowserTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_BabyBrowser1()

  def test_BabyBrowser1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = BabyBrowserLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
