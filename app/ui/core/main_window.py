# -*- coding: utf-8 -*-
################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING
################################################################################
from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from app.ui.core import media_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1548, 768)
        font = QFont()
        font.setPointSize(10)
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(
            ":/media/media/visomaster_small.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        MainWindow.setWindowIcon(icon)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionLoad_Embeddings = QAction(MainWindow)
        self.actionLoad_Embeddings.setObjectName("actionLoad_Embeddings")
        self.actionSave_Embeddings = QAction(MainWindow)
        self.actionSave_Embeddings.setObjectName("actionSave_Embeddings")
        self.actionSave_Embeddings_As = QAction(MainWindow)
        self.actionSave_Embeddings_As.setObjectName("actionSave_Embeddings_As")
        self.actionOpen_Videos_Folder = QAction(MainWindow)
        self.actionOpen_Videos_Folder.setObjectName("actionOpen_Videos_Folder")
        self.actionOpen_Video_Files = QAction(MainWindow)
        self.actionOpen_Video_Files.setObjectName("actionOpen_Video_Files")
        self.actionLoad_Source_Images_Folder = QAction(MainWindow)
        self.actionLoad_Source_Images_Folder.setObjectName(
            "actionLoad_Source_Images_Folder"
        )
        self.actionLoad_Source_Image_Files = QAction(MainWindow)
        self.actionLoad_Source_Image_Files.setObjectName(
            "actionLoad_Source_Image_Files"
        )
        self.actionView_Fullscreen_F11 = QAction(MainWindow)
        self.actionView_Fullscreen_F11.setObjectName("actionView_Fullscreen_F11")
        self.actionView_Help_Shortcuts = QAction(MainWindow)
        self.actionView_Help_Shortcuts.setObjectName("actionView_Help_Shortcuts")
        self.actionView_Help_Presets = QAction(MainWindow)
        self.actionView_Help_Presets.setObjectName("actionView_Help_Presets")
        self.actionTest = QAction(MainWindow)
        self.actionTest.setObjectName("actionTest")
        self.actionLoad_Saved_Workspace = QAction(MainWindow)
        self.actionLoad_Saved_Workspace.setObjectName("actionLoad_Saved_Workspace")
        self.actionSave_Current_Workspace = QAction(MainWindow)
        self.actionSave_Current_Workspace.setObjectName("actionSave_Current_Workspace")
        self.actionTest_2 = QAction(MainWindow)
        self.actionTest_2.setObjectName("actionTest_2")
        self.actionLoad_SavedWorkspace = QAction(MainWindow)
        self.actionLoad_SavedWorkspace.setObjectName("actionLoad_SavedWorkspace")
        self.actionSave_CurrentWorkspace = QAction(MainWindow)
        self.actionSave_CurrentWorkspace.setObjectName("actionSave_CurrentWorkspace")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mediaLayout = QWidget(self.centralwidget)
        self.mediaLayout.setObjectName("mediaLayout")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mediaLayout.sizePolicy().hasHeightForWidth())
        self.mediaLayout.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.mediaLayout)
        self.verticalLayout.setObjectName("verticalLayout")
        self.panelVisibilityCheckBoxLayout = QHBoxLayout()
        self.panelVisibilityCheckBoxLayout.setObjectName(
            "panelVisibilityCheckBoxLayout"
        )
        self.TargetMediaCheckBox = QCheckBox(self.mediaLayout)
        self.TargetMediaCheckBox.setObjectName("TargetMediaCheckBox")
        self.TargetMediaCheckBox.setChecked(True)
        self.panelVisibilityCheckBoxLayout.addWidget(self.TargetMediaCheckBox)
        self.InputFacesCheckBox = QCheckBox(self.mediaLayout)
        self.InputFacesCheckBox.setObjectName("InputFacesCheckBox")
        self.InputFacesCheckBox.setChecked(True)
        self.panelVisibilityCheckBoxLayout.addWidget(self.InputFacesCheckBox)
        self.JobsCheckBox = QCheckBox(self.mediaLayout)
        self.JobsCheckBox.setObjectName("JobsCheckBox")
        self.JobsCheckBox.setChecked(True)
        self.panelVisibilityCheckBoxLayout.addWidget(self.JobsCheckBox)
        self.facesPanelCheckBox = QCheckBox(self.mediaLayout)
        self.facesPanelCheckBox.setObjectName("facesPanelCheckBox")
        self.facesPanelCheckBox.setChecked(True)
        self.panelVisibilityCheckBoxLayout.addWidget(self.facesPanelCheckBox)
        self.parametersPanelCheckBox = QCheckBox(self.mediaLayout)
        self.parametersPanelCheckBox.setObjectName("parametersPanelCheckBox")
        self.parametersPanelCheckBox.setChecked(True)
        self.panelVisibilityCheckBoxLayout.addWidget(self.parametersPanelCheckBox)
        self.horizontalSpacer_8 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.panelVisibilityCheckBoxLayout.addItem(self.horizontalSpacer_8)
        self.faceCompareCheckBox = QCheckBox(self.mediaLayout)
        self.faceCompareCheckBox.setObjectName("faceCompareCheckBox")
        self.panelVisibilityCheckBoxLayout.addWidget(self.faceCompareCheckBox)
        self.faceMaskCheckBox = QCheckBox(self.mediaLayout)
        self.faceMaskCheckBox.setObjectName("faceMaskCheckBox")
        self.panelVisibilityCheckBoxLayout.addWidget(self.faceMaskCheckBox)
        self.verticalLayout.addLayout(self.panelVisibilityCheckBoxLayout)
        self.graphicsViewFrame = QGraphicsView(self.mediaLayout)
        self.graphicsViewFrame.setObjectName("graphicsViewFrame")
        self.verticalLayout.addWidget(self.graphicsViewFrame)
        self.verticalLayoutMediaControls = QVBoxLayout()
        self.verticalLayoutMediaControls.setObjectName("verticalLayoutMediaControls")
        self.horizontalLayoutMediaSlider = QHBoxLayout()
        self.horizontalLayoutMediaSlider.setObjectName("horizontalLayoutMediaSlider")
        self.videoSeekSlider = QSlider(self.mediaLayout)
        self.videoSeekSlider.setObjectName("videoSeekSlider")
        self.videoSeekSlider.setOrientation(Qt.Orientation.Horizontal)
        self.horizontalLayoutMediaSlider.addWidget(self.videoSeekSlider)
        self.videoSeekLineEdit = QLineEdit(self.mediaLayout)
        self.videoSeekLineEdit.setObjectName("videoSeekLineEdit")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.videoSeekLineEdit.sizePolicy().hasHeightForWidth()
        )
        self.videoSeekLineEdit.setSizePolicy(sizePolicy1)
        self.videoSeekLineEdit.setMaximumSize(QSize(70, 16777215))
        self.videoSeekLineEdit.setClearButtonEnabled(False)
        self.horizontalLayoutMediaSlider.addWidget(self.videoSeekLineEdit)
        self.verticalLayoutMediaControls.addLayout(self.horizontalLayoutMediaSlider)
        self.horizontalLayoutMediaButtons = QHBoxLayout()
        self.horizontalLayoutMediaButtons.setObjectName("horizontalLayoutMediaButtons")
        self.horizontalSpacer_7 = QSpacerItem(
            40, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_7)
        self.liveSoundButton = QPushButton(self.mediaLayout)
        self.liveSoundButton.setObjectName("liveSoundButton")
        self.liveSoundButton.setMinimumSize(QSize(0, 0))
        icon1 = QIcon()
        icon1.addFile(
            ":/media/media/audio_off.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.liveSoundButton.setIcon(icon1)
        self.liveSoundButton.setIconSize(QSize(16, 20))
        self.liveSoundButton.setCheckable(True)
        self.liveSoundButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.liveSoundButton)
        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer)
        self.frameRewindButton = QPushButton(self.mediaLayout)
        self.frameRewindButton.setObjectName("frameRewindButton")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.frameRewindButton.sizePolicy().hasHeightForWidth()
        )
        self.frameRewindButton.setSizePolicy(sizePolicy2)
        self.frameRewindButton.setMaximumSize(QSize(100, 16777215))
        icon2 = QIcon()
        icon2.addFile(
            ":/media/media/tl_left_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.frameRewindButton.setIcon(icon2)
        self.frameRewindButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.frameRewindButton)
        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_3)
        self.buttonMediaRecord = QPushButton(self.mediaLayout)
        self.buttonMediaRecord.setObjectName("buttonMediaRecord")
        icon3 = QIcon()
        icon3.addFile(
            ":/media/media/rec_off.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.buttonMediaRecord.setIcon(icon3)
        self.buttonMediaRecord.setCheckable(True)
        self.buttonMediaRecord.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.buttonMediaRecord)
        self.horizontalSpacer_6 = QSpacerItem(
            30, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_6)
        self.buttonMediaPlay = QPushButton(self.mediaLayout)
        self.buttonMediaPlay.setObjectName("buttonMediaPlay")
        sizePolicy3 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(
            self.buttonMediaPlay.sizePolicy().hasHeightForWidth()
        )
        self.buttonMediaPlay.setSizePolicy(sizePolicy3)
        self.buttonMediaPlay.setMaximumSize(QSize(100, 16777215))
        icon4 = QIcon()
        icon4.addFile(
            ":/media/media/play_hover.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.buttonMediaPlay.setIcon(icon4)
        self.buttonMediaPlay.setCheckable(True)
        self.buttonMediaPlay.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.buttonMediaPlay)
        self.horizontalSpacer_4 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_4)
        self.frameAdvanceButton = QPushButton(self.mediaLayout)
        self.frameAdvanceButton.setObjectName("frameAdvanceButton")
        sizePolicy2.setHeightForWidth(
            self.frameAdvanceButton.sizePolicy().hasHeightForWidth()
        )
        self.frameAdvanceButton.setSizePolicy(sizePolicy2)
        self.frameAdvanceButton.setMaximumSize(QSize(100, 16777215))
        icon5 = QIcon()
        icon5.addFile(
            ":/media/media/tl_right_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.frameAdvanceButton.setIcon(icon5)
        self.frameAdvanceButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.frameAdvanceButton)
        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_2)
        self.addMarkerButton = QPushButton(self.mediaLayout)
        self.addMarkerButton.setObjectName("addMarkerButton")
        icon6 = QIcon()
        icon6.addFile(
            ":/media/media/add_marker_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.addMarkerButton.setIcon(icon6)
        self.addMarkerButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.addMarkerButton)
        self.removeMarkerButton = QPushButton(self.mediaLayout)
        self.removeMarkerButton.setObjectName("removeMarkerButton")
        icon7 = QIcon()
        icon7.addFile(
            ":/media/media/remove_marker_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.removeMarkerButton.setIcon(icon7)
        self.removeMarkerButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.removeMarkerButton)
        self.previousMarkerButton = QPushButton(self.mediaLayout)
        self.previousMarkerButton.setObjectName("previousMarkerButton")
        icon8 = QIcon()
        icon8.addFile(
            ":/media/media/previous_marker_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.previousMarkerButton.setIcon(icon8)
        self.previousMarkerButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.previousMarkerButton)
        self.nextMarkerButton = QPushButton(self.mediaLayout)
        self.nextMarkerButton.setObjectName("nextMarkerButton")
        icon9 = QIcon()
        icon9.addFile(
            ":/media/media/next_marker_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.nextMarkerButton.setIcon(icon9)
        self.nextMarkerButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.nextMarkerButton)
        self.viewFullScreenButton = QPushButton(self.mediaLayout)
        self.viewFullScreenButton.setObjectName("viewFullScreenButton")
        icon10 = QIcon()
        icon10.addFile(
            ":/media/media/fullscreen.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.viewFullScreenButton.setIcon(icon10)
        self.viewFullScreenButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.viewFullScreenButton)
        self.theatreModeButton = QPushButton(self.mediaLayout)
        self.theatreModeButton.setObjectName("theatreModeButton")
        icon11 = QIcon()
        icon11.addFile(
            ":/media/media/theatre_hover.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.theatreModeButton.setIcon(icon11)
        self.theatreModeButton.setFlat(True)
        self.horizontalLayoutMediaButtons.addWidget(self.theatreModeButton)
        self.horizontalSpacer_5 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.horizontalLayoutMediaButtons.addItem(self.horizontalSpacer_5)
        self.verticalLayoutMediaControls.addLayout(self.horizontalLayoutMediaButtons)
        self.verticalLayout.addLayout(self.verticalLayoutMediaControls)
        self.verticalSpacer = QSpacerItem(
            20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        self.verticalLayout.addItem(self.verticalSpacer)
        self.facesPanelGroupBox = QGroupBox(self.mediaLayout)
        self.facesPanelGroupBox.setObjectName("facesPanelGroupBox")
        sizePolicy4 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(
            self.facesPanelGroupBox.sizePolicy().hasHeightForWidth()
        )
        self.facesPanelGroupBox.setSizePolicy(sizePolicy4)
        self.facesPanelGroupBox.setMinimumSize(QSize(0, 220))
        self.facesPanelGroupBox.setMaximumSize(QSize(16777215, 16777215))
        self.facesPanelGroupBox.setAutoFillBackground(False)
        self.facesPanelGroupBox.setFlat(True)
        self.facesPanelGroupBox.setCheckable(False)
        self.gridLayout_2 = QGridLayout(self.facesPanelGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.facesButtonsWidget = QWidget(self.facesPanelGroupBox)
        self.facesButtonsWidget.setObjectName("facesButtonsWidget")
        sizePolicy5 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(
            self.facesButtonsWidget.sizePolicy().hasHeightForWidth()
        )
        self.facesButtonsWidget.setSizePolicy(sizePolicy5)
        self.verticalLayout_8 = QVBoxLayout(self.facesButtonsWidget)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalWidget = QWidget(self.facesButtonsWidget)
        self.verticalWidget.setObjectName("verticalWidget")
        self.controlButtonsLayout = QVBoxLayout(self.verticalWidget)
        self.controlButtonsLayout.setSpacing(8)
        self.controlButtonsLayout.setObjectName("controlButtonsLayout")
        self.controlButtonsLayout.setContentsMargins(0, 4, 0, 4)
        self.findTargetFacesButton = QPushButton(self.verticalWidget)
        self.findTargetFacesButton.setObjectName("findTargetFacesButton")
        self.findTargetFacesButton.setMinimumSize(QSize(100, 0))
        self.findTargetFacesButton.setCheckable(False)
        self.findTargetFacesButton.setFlat(True)
        self.controlButtonsLayout.addWidget(self.findTargetFacesButton)
        self.clearTargetFacesButton = QPushButton(self.verticalWidget)
        self.clearTargetFacesButton.setObjectName("clearTargetFacesButton")
        self.clearTargetFacesButton.setCheckable(False)
        self.clearTargetFacesButton.setFlat(True)
        self.controlButtonsLayout.addWidget(self.clearTargetFacesButton)
        self.swapfacesButton = QPushButton(self.verticalWidget)
        self.swapfacesButton.setObjectName("swapfacesButton")
        self.swapfacesButton.setCheckable(True)
        self.swapfacesButton.setFlat(True)
        self.controlButtonsLayout.addWidget(self.swapfacesButton)
        self.editFacesButton = QPushButton(self.verticalWidget)
        self.editFacesButton.setObjectName("editFacesButton")
        self.editFacesButton.setCheckable(True)
        self.editFacesButton.setFlat(True)
        self.controlButtonsLayout.addWidget(self.editFacesButton)
        self.verticalLayout_8.addWidget(self.verticalWidget)
        self.gridLayout_2.addWidget(self.facesButtonsWidget, 1, 0, 1, 1)
        self.inputEmbeddingsList = QListWidget(self.facesPanelGroupBox)
        self.inputEmbeddingsList.setObjectName("inputEmbeddingsList")
        sizePolicy6 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy6.setHorizontalStretch(4)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(
            self.inputEmbeddingsList.sizePolicy().hasHeightForWidth()
        )
        self.inputEmbeddingsList.setSizePolicy(sizePolicy6)
        self.inputEmbeddingsList.setMinimumSize(QSize(320, 120))
        self.inputEmbeddingsList.setMaximumSize(QSize(16777215, 120))
        self.inputEmbeddingsList.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.inputEmbeddingsList.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.inputEmbeddingsList.setAutoScroll(False)
        self.inputEmbeddingsList.setMovement(QListView.Movement.Static)
        self.inputEmbeddingsList.setLayoutMode(QListView.LayoutMode.Batched)
        self.inputEmbeddingsList.setSpacing(4)
        self.inputEmbeddingsList.setViewMode(QListView.ViewMode.IconMode)
        self.inputEmbeddingsList.setUniformItemSizes(True)
        self.inputEmbeddingsList.setProperty("wrapping", True)
        self.gridLayout_2.addWidget(self.inputEmbeddingsList, 1, 2, 1, 1)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.saveImageButton = QPushButton(self.facesPanelGroupBox)
        self.saveImageButton.setObjectName("saveImageButton")
        self.saveImageButton.setFlat(True)
        self.horizontalLayout_4.addWidget(self.saveImageButton)
        self.gridLayout_2.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)
        self.batchLayout_1 = QHBoxLayout()
        self.batchLayout_1.setObjectName("batchLayout_1")
        self.batchImageButton = QPushButton(self.facesPanelGroupBox)
        self.batchImageButton.setObjectName("batchImageButton")
        self.batchImageButton.setFlat(True)
        self.batchLayout_1.addWidget(self.batchImageButton)
        self.batchallImageButton = QPushButton(self.facesPanelGroupBox)
        self.batchallImageButton.setObjectName("batchallImageButton")
        self.batchallImageButton.setFlat(True)
        self.batchLayout_1.addWidget(self.batchallImageButton)
        self.gridLayout_2.addLayout(self.batchLayout_1, 0, 1, 1, 1)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.inputEmbeddingsSearchBox = QLineEdit(self.facesPanelGroupBox)
        self.inputEmbeddingsSearchBox.setObjectName("inputEmbeddingsSearchBox")
        self.horizontalLayout_3.addWidget(self.inputEmbeddingsSearchBox)
        self.openEditorButton = QPushButton(self.facesPanelGroupBox)
        self.openEditorButton.setObjectName("openEditorButton")
        self.openEditorButton.setCheckable(False)
        self.openEditorButton.setFlat(True)
        self.horizontalLayout_3.addWidget(self.openEditorButton)
        self.openEmbeddingButton = QPushButton(self.facesPanelGroupBox)
        self.openEmbeddingButton.setObjectName("openEmbeddingButton")
        icon12 = QIcon()
        icon12.addFile(
            ":/media/media/open_file.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.openEmbeddingButton.setIcon(icon12)
        self.openEmbeddingButton.setFlat(True)
        self.horizontalLayout_3.addWidget(self.openEmbeddingButton)
        self.saveEmbeddingButton = QPushButton(self.facesPanelGroupBox)
        self.saveEmbeddingButton.setObjectName("saveEmbeddingButton")
        icon13 = QIcon()
        icon13.addFile(
            ":/media/media/save_file.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.saveEmbeddingButton.setIcon(icon13)
        self.saveEmbeddingButton.setFlat(True)
        self.horizontalLayout_3.addWidget(self.saveEmbeddingButton)
        self.saveEmbeddingAsButton = QPushButton(self.facesPanelGroupBox)
        self.saveEmbeddingAsButton.setObjectName("saveEmbeddingAsButton")
        icon14 = QIcon()
        icon14.addFile(
            ":/media/media/save_file_as.png",
            QSize(),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.saveEmbeddingAsButton.setIcon(icon14)
        self.saveEmbeddingAsButton.setFlat(True)
        self.horizontalLayout_3.addWidget(self.saveEmbeddingAsButton)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 2, 1, 1)
        self.targetFacesList = QListWidget(self.facesPanelGroupBox)
        self.targetFacesList.setObjectName("targetFacesList")
        self.targetFacesList.setAutoFillBackground(True)
        self.targetFacesList.setAutoScroll(False)
        self.gridLayout_2.addWidget(self.targetFacesList, 1, 1, 1, 1)
        self.verticalLayout.addWidget(self.facesPanelGroupBox)
        self.horizontalLayout.addWidget(self.mediaLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.input_Target_DockWidget = QDockWidget(MainWindow)
        self.input_Target_DockWidget.setObjectName("input_Target_DockWidget")
        sizePolicy7 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy7.setHorizontalStretch(4)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(
            self.input_Target_DockWidget.sizePolicy().hasHeightForWidth()
        )
        self.input_Target_DockWidget.setSizePolicy(sizePolicy7)
        self.input_Target_DockWidget.setMinimumSize(QSize(324, 230))
        self.input_Target_DockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout_4 = QGridLayout(self.dockWidgetContents)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.vboxLayout = QVBoxLayout()
        self.vboxLayout.setObjectName("vboxLayout")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.targetVideosPathLineEdit = QLineEdit(self.dockWidgetContents)
        self.targetVideosPathLineEdit.setObjectName("targetVideosPathLineEdit")
        self.targetVideosPathLineEdit.setReadOnly(True)
        self.horizontalLayout_7.addWidget(self.targetVideosPathLineEdit)
        self.buttonTargetVideosPath = QPushButton(self.dockWidgetContents)
        self.buttonTargetVideosPath.setObjectName("buttonTargetVideosPath")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(
            self.buttonTargetVideosPath.sizePolicy().hasHeightForWidth()
        )
        self.buttonTargetVideosPath.setSizePolicy(sizePolicy8)
        self.buttonTargetVideosPath.setIconSize(QSize(18, 18))
        self.buttonTargetVideosPath.setFlat(True)
        self.horizontalLayout_7.addWidget(self.buttonTargetVideosPath)
        self.vboxLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.targetVideosSearchBox = QLineEdit(self.dockWidgetContents)
        self.targetVideosSearchBox.setObjectName("targetVideosSearchBox")
        self.horizontalLayout_9.addWidget(self.targetVideosSearchBox)
        self.targetVideosFilterMenuButton = QPushButton(self.dockWidgetContents)
        self.targetVideosFilterMenuButton.setObjectName("targetVideosFilterMenuButton")
        icon15 = QIcon()
        icon15.addFile(
            ":/media/media/filter.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.targetVideosFilterMenuButton.setIcon(icon15)
        self.targetVideosFilterMenuButton.setIconSize(QSize(18, 18))
        self.targetVideosFilterMenuButton.setFlat(True)
        self.horizontalLayout_9.addWidget(self.targetVideosFilterMenuButton)
        self.vboxLayout.addLayout(self.horizontalLayout_9)
        self.targetVideosList = QListWidget(self.dockWidgetContents)
        self.targetVideosList.setObjectName("targetVideosList")
        self.targetVideosList.setAcceptDrops(True)
        self.targetVideosList.setAutoScroll(False)
        self.vboxLayout.addWidget(self.targetVideosList)
        self.gridLayout_4.addLayout(self.vboxLayout, 0, 0, 1, 1)
        self.input_Target_DockWidget.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.input_Target_DockWidget
        )
        self.input_Faces_DockWidget = QDockWidget(MainWindow)
        self.input_Faces_DockWidget.setObjectName("input_Faces_DockWidget")
        sizePolicy7.setHeightForWidth(
            self.input_Faces_DockWidget.sizePolicy().hasHeightForWidth()
        )
        self.input_Faces_DockWidget.setSizePolicy(sizePolicy7)
        self.input_Faces_DockWidget.setMinimumSize(QSize(340, 230))
        self.input_Faces_DockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidgetContents_Faces = QWidget()
        self.dockWidgetContents_Faces.setObjectName("dockWidgetContents_Faces")
        self.gridLayout_Faces = QGridLayout(self.dockWidgetContents_Faces)
        self.gridLayout_Faces.setObjectName("gridLayout_Faces")
        self.vboxLayout_Faces = QVBoxLayout()
        self.vboxLayout_Faces.setObjectName("vboxLayout_Faces")
        self.horizontalLayout_Faces = QHBoxLayout()
        self.horizontalLayout_Faces.setObjectName("horizontalLayout_Faces")
        self.inputFacesPathLineEdit = QLineEdit(self.dockWidgetContents_Faces)
        self.inputFacesPathLineEdit.setObjectName("inputFacesPathLineEdit")
        self.inputFacesPathLineEdit.setReadOnly(True)
        self.horizontalLayout_Faces.addWidget(self.inputFacesPathLineEdit)
        self.buttonInputFacesPath = QPushButton(self.dockWidgetContents_Faces)
        self.buttonInputFacesPath.setObjectName("buttonInputFacesPath")
        sizePolicy8.setHeightForWidth(
            self.buttonInputFacesPath.sizePolicy().hasHeightForWidth()
        )
        self.buttonInputFacesPath.setSizePolicy(sizePolicy8)
        self.buttonInputFacesPath.setIconSize(QSize(18, 18))
        self.buttonInputFacesPath.setFlat(True)
        self.horizontalLayout_Faces.addWidget(self.buttonInputFacesPath)
        self.vboxLayout_Faces.addLayout(self.horizontalLayout_Faces)
        self.inputFacesSearchBox = QLineEdit(self.dockWidgetContents_Faces)
        self.inputFacesSearchBox.setObjectName("inputFacesSearchBox")
        self.vboxLayout_Faces.addWidget(self.inputFacesSearchBox)
        self.inputFacesList = QListWidget(self.dockWidgetContents_Faces)
        self.inputFacesList.setObjectName("inputFacesList")
        self.inputFacesList.setAcceptDrops(True)
        self.inputFacesList.setAutoScroll(False)
        self.vboxLayout_Faces.addWidget(self.inputFacesList)
        self.gridLayout_Faces.addLayout(self.vboxLayout_Faces, 0, 0, 1, 1)
        self.input_Faces_DockWidget.setWidget(self.dockWidgetContents_Faces)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.input_Faces_DockWidget
        )
        self.jobManagerDockWidget = QDockWidget(MainWindow)
        self.jobManagerDockWidget.setObjectName("jobManagerDockWidget")
        self.jobManagerDockWidget.setMinimumSize(QSize(324, 230))
        self.jobManagerDockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidgetContents_JobManager = QWidget()
        self.dockWidgetContents_JobManager.setObjectName(
            "dockWidgetContents_JobManager"
        )
        self.verticalLayout_JobManager = QVBoxLayout(self.dockWidgetContents_JobManager)
        self.verticalLayout_JobManager.setObjectName("verticalLayout_JobManager")
        self.jobControlLayout = QHBoxLayout()
        self.jobControlLayout.setObjectName("jobControlLayout")
        self.addJobButton = QPushButton(self.dockWidgetContents_JobManager)
        self.addJobButton.setObjectName("addJobButton")
        self.jobControlLayout.addWidget(self.addJobButton)
        self.loadJobButton = QPushButton(self.dockWidgetContents_JobManager)
        self.loadJobButton.setObjectName("loadJobButton")
        self.jobControlLayout.addWidget(self.loadJobButton)
        self.deleteJobButton = QPushButton(self.dockWidgetContents_JobManager)
        self.deleteJobButton.setObjectName("deleteJobButton")
        self.jobControlLayout.addWidget(self.deleteJobButton)
        self.verticalLayout_JobManager.addLayout(self.jobControlLayout)
        self.refreshJobListButton = QPushButton(self.dockWidgetContents_JobManager)
        self.refreshJobListButton.setObjectName("refreshJobListButton")
        self.verticalLayout_JobManager.addWidget(self.refreshJobListButton)
        self.jobQueueList = QListWidget(self.dockWidgetContents_JobManager)
        self.jobQueueList.setObjectName("jobQueueList")
        self.jobQueueList.setSortingEnabled(True)
        self.verticalLayout_JobManager.addWidget(self.jobQueueList)
        self.processControlLayout = QHBoxLayout()
        self.processControlLayout.setObjectName("processControlLayout")
        self.buttonProcessAll = QPushButton(self.dockWidgetContents_JobManager)
        self.buttonProcessAll.setObjectName("buttonProcessAll")
        self.processControlLayout.addWidget(self.buttonProcessAll)
        self.buttonProcessSelected = QPushButton(self.dockWidgetContents_JobManager)
        self.buttonProcessSelected.setObjectName("buttonProcessSelected")
        self.processControlLayout.addWidget(self.buttonProcessSelected)
        self.verticalLayout_JobManager.addLayout(self.processControlLayout)
        self.jobManagerDockWidget.setWidget(self.dockWidgetContents_JobManager)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.jobManagerDockWidget
        )
        self.controlOptionsDockWidget = QDockWidget(MainWindow)
        self.controlOptionsDockWidget.setObjectName("controlOptionsDockWidget")
        self.controlOptionsDockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.gridLayout_5 = QGridLayout(self.dockWidgetContents_2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.tabWidget = QTabWidget(self.dockWidgetContents_2)
        self.tabWidget.setObjectName("tabWidget")
        sizePolicy9 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy9.setHorizontalStretch(1)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy9)
        font1 = QFont()
        font1.setFamilies(["Segoe UI Semibold"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.tabWidget.setFont(font1)
        self.tabWidget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabBarAutoHide(False)
        self.face_swap_tab = QWidget()
        self.face_swap_tab.setObjectName("face_swap_tab")
        self.verticalLayout_4 = QVBoxLayout(self.face_swap_tab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.swapWidgetsLayout = QVBoxLayout()
        self.swapWidgetsLayout.setObjectName("swapWidgetsLayout")
        self.verticalLayout_4.addLayout(self.swapWidgetsLayout)
        self.tabWidget.addTab(self.face_swap_tab, "")
        self.face_editor_tab = QWidget()
        self.face_editor_tab.setObjectName("face_editor_tab")
        self.verticalLayout_3 = QVBoxLayout(self.face_editor_tab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.faceEditorWidgetsLayout = QVBoxLayout()
        self.faceEditorWidgetsLayout.setObjectName("faceEditorWidgetsLayout")
        self.verticalLayout_3.addLayout(self.faceEditorWidgetsLayout)
        self.tabWidget.addTab(self.face_editor_tab, "")
        self.common_tab = QWidget()
        self.common_tab.setObjectName("common_tab")
        self.commonWidgetsLayout_1 = QVBoxLayout(self.common_tab)
        self.commonWidgetsLayout_1.setObjectName("commonWidgetsLayout_1")
        self.commonWidgetsLayout = QVBoxLayout()
        self.commonWidgetsLayout.setObjectName("commonWidgetsLayout")
        self.commonWidgetsLayout_1.addLayout(self.commonWidgetsLayout)
        self.tabWidget.addTab(self.common_tab, "")
        self.denoiser_tab = QWidget()
        self.denoiser_tab.setObjectName("denoiser_tab")
        self.denoiserWidgetsLayout_1 = QVBoxLayout(self.denoiser_tab)
        self.denoiserWidgetsLayout_1.setObjectName("denoiserWidgetsLayout_1")
        self.denoiserWidgetsLayout = QVBoxLayout()
        self.denoiserWidgetsLayout.setObjectName("denoiserWidgetsLayout")
        self.denoiserWidgetsLayout_1.addLayout(self.denoiserWidgetsLayout)
        self.tabWidget.addTab(self.denoiser_tab, "")
        self.settings_tab = QWidget()
        self.settings_tab.setObjectName("settings_tab")
        self.verticalLayout_2 = QVBoxLayout(self.settings_tab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QLabel(self.settings_tab)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.settingsWidgetsLayout = QVBoxLayout()
        self.settingsWidgetsLayout.setObjectName("settingsWidgetsLayout")
        self.outputFolderSelectionLayout = QHBoxLayout()
        self.outputFolderSelectionLayout.setObjectName("outputFolderSelectionLayout")
        self.outputFolderLineEdit = QLineEdit(self.settings_tab)
        self.outputFolderLineEdit.setObjectName("outputFolderLineEdit")
        self.outputFolderLineEdit.setReadOnly(True)
        self.outputFolderSelectionLayout.addWidget(self.outputFolderLineEdit)
        self.outputFolderButton = QPushButton(self.settings_tab)
        self.outputFolderButton.setObjectName("outputFolderButton")
        self.outputFolderButton.setFlat(False)
        self.outputFolderSelectionLayout.addWidget(self.outputFolderButton)
        self.outputOpenButton = QPushButton(self.settings_tab)
        self.outputOpenButton.setObjectName("outputOpenButton")
        self.outputOpenButton.setFlat(False)
        self.outputFolderSelectionLayout.addWidget(self.outputOpenButton)
        self.settingsWidgetsLayout.addLayout(self.outputFolderSelectionLayout)
        self.verticalLayout_2.addLayout(self.settingsWidgetsLayout)
        self.tabWidget.addTab(self.settings_tab, "")
        self.preset_tab = QWidget()
        self.preset_tab.setObjectName("preset_tab")
        self.presetsWidgetsLayout_1 = QVBoxLayout(self.preset_tab)
        self.presetsWidgetsLayout_1.setObjectName("presetsWidgetsLayout_1")
        self.labelp = QLabel(self.preset_tab)
        self.labelp.setObjectName("labelp")
        self.presetsWidgetsLayout_1.addWidget(self.labelp)
        self.presetsWidgetsLayout = QVBoxLayout()
        self.presetsWidgetsLayout.setObjectName("presetsWidgetsLayout")
        self.presetsList = QListWidget(self.preset_tab)
        self.presetsList.setObjectName("presetsList")
        self.presetsList.setSortingEnabled(True)
        self.presetsList.setMinimumSize(QSize(0, 360))
        self.presetsList.setMaximumSize(QSize(16777215, 460))
        self.presetsWidgetsLayout.addWidget(self.presetsList)
        self.presetsButtonsLayout = QHBoxLayout()
        self.presetsButtonsLayout.setObjectName("presetsButtonsLayout")
        self.applyPresetButton = QPushButton(self.preset_tab)
        self.applyPresetButton.setObjectName("applyPresetButton")
        self.presetsButtonsLayout.addWidget(self.applyPresetButton)
        self.savePresetButton = QPushButton(self.preset_tab)
        self.savePresetButton.setObjectName("savePresetButton")
        self.presetsButtonsLayout.addWidget(self.savePresetButton)
        self.controlPresetButton = QPushButton(self.preset_tab)
        self.controlPresetButton.setObjectName("controlPresetButton")
        self.controlPresetButton.setCheckable(True)
        self.presetsButtonsLayout.addWidget(self.controlPresetButton)
        self.presetsWidgetsLayout.addLayout(self.presetsButtonsLayout)
        self.presetsWidgetsLayout_1.addLayout(self.presetsWidgetsLayout)
        self.verticalSpacerpresets = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.presetsWidgetsLayout_1.addItem(self.verticalSpacerpresets)
        self.tabWidget.addTab(self.preset_tab, "")
        self.gridLayout_5.addWidget(self.tabWidget, 1, 0, 1, 1)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.vramProgressBar = QProgressBar(self.dockWidgetContents_2)
        self.vramProgressBar.setObjectName("vramProgressBar")
        self.vramProgressBar.setValue(24)
        self.horizontalLayout_2.addWidget(self.vramProgressBar)
        self.clearMemoryButton = QPushButton(self.dockWidgetContents_2)
        self.clearMemoryButton.setObjectName("clearMemoryButton")
        self.clearMemoryButton.setFlat(True)
        self.horizontalLayout_2.addWidget(self.clearMemoryButton)
        self.gridLayout_5.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.controlOptionsDockWidget.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.controlOptionsDockWidget
        )
        self.topMenuBar = QMenuBar(MainWindow)
        self.topMenuBar.setObjectName("topMenuBar")
        self.topMenuBar.setGeometry(QRect(0, 0, 1376, 33))
        self.menuFile = QMenu(self.topMenuBar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QMenu(self.topMenuBar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QMenu(self.topMenuBar)
        self.menuView.setObjectName("menuView")
        self.menuHelp = QMenu(self.topMenuBar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.topMenuBar)
        self.topMenuBar.addAction(self.menuFile.menuAction())
        self.topMenuBar.addAction(self.menuEdit.menuAction())
        self.topMenuBar.addAction(self.menuView.menuAction())
        self.topMenuBar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionLoad_SavedWorkspace)
        self.menuFile.addAction(self.actionSave_CurrentWorkspace)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOpen_Videos_Folder)
        self.menuFile.addAction(self.actionOpen_Video_Files)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionLoad_Source_Images_Folder)
        self.menuFile.addAction(self.actionLoad_Source_Image_Files)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionLoad_Embeddings)
        self.menuFile.addAction(self.actionSave_Embeddings)
        self.menuFile.addAction(self.actionSave_Embeddings_As)
        self.menuEdit.addAction(self.actionTest_2)
        self.menuView.addAction(self.actionView_Fullscreen_F11)
        self.menuHelp.addAction(self.actionView_Help_Shortcuts)
        self.menuHelp.addAction(self.actionView_Help_Presets)
        self.retranslateUi(MainWindow)
        self.editFacesButton.setDefault(False)
        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate(
                "MainWindow", "VisoMaster - Fusion", None
            )
        )
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionLoad_Embeddings.setText(
            QCoreApplication.translate("MainWindow", "Load Embeddings", None)
        )
        self.actionSave_Embeddings.setText(
            QCoreApplication.translate("MainWindow", "Save Embeddings", None)
        )
        self.actionSave_Embeddings_As.setText(
            QCoreApplication.translate("MainWindow", "Save Embeddings As", None)
        )
        self.actionOpen_Videos_Folder.setText(
            QCoreApplication.translate(
                "MainWindow", "Load Target Images/Videos Folder", None
            )
        )
        self.actionOpen_Video_Files.setText(
            QCoreApplication.translate(
                "MainWindow", "Load Target Image/Video Files", None
            )
        )
        self.actionLoad_Source_Images_Folder.setText(
            QCoreApplication.translate("MainWindow", "Load Source Images Folder", None)
        )
        self.actionLoad_Source_Image_Files.setText(
            QCoreApplication.translate("MainWindow", "Load Source Image Files", None)
        )
        self.actionView_Fullscreen_F11.setText(
            QCoreApplication.translate("MainWindow", "Fullscreen", None)
        )
        self.actionView_Help_Shortcuts.setText(
            QCoreApplication.translate("MainWindow", "View Shortcuts", None)
        )
        self.actionView_Help_Presets.setText(
            QCoreApplication.translate("MainWindow", "Presets", None)
        )
        self.actionTest.setText(QCoreApplication.translate("MainWindow", "Test", None))
        self.actionLoad_Saved_Workspace.setText(
            QCoreApplication.translate("MainWindow", "Load Saved Workspace", None)
        )
        self.actionSave_Current_Workspace.setText(
            QCoreApplication.translate("MainWindow", "Save Current Workspace", None)
        )
        self.actionTest_2.setText(
            QCoreApplication.translate("MainWindow", "Test", None)
        )
        self.actionLoad_SavedWorkspace.setText(
            QCoreApplication.translate("MainWindow", "Load Saved Workspace", None)
        )
        self.actionSave_CurrentWorkspace.setText(
            QCoreApplication.translate("MainWindow", "Save Current Workspace", None)
        )
        self.TargetMediaCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Target Videos/Images", None)
        )
        self.InputFacesCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Input Faces", None)
        )
        self.JobsCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Jobs", None)
        )
        self.facesPanelCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Faces", None)
        )
        self.parametersPanelCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Parameters", None)
        )
        self.faceCompareCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Face Compare", None)
        )
        self.faceMaskCheckBox.setText(
            QCoreApplication.translate("MainWindow", "Face Mask", None)
        )
        # if QT_CONFIG(tooltip)
        self.videoSeekLineEdit.setToolTip(
            QCoreApplication.translate("MainWindow", "Frame Number", None)
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.liveSoundButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "[Experimental] Toggle Live Sound while the video is playing",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.liveSoundButton.setText("")
        self.frameRewindButton.setText("")
        self.buttonMediaRecord.setText("")
        self.buttonMediaPlay.setText("")
        self.frameAdvanceButton.setText("")
        # if QT_CONFIG(tooltip)
        self.addMarkerButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Add Marker", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.addMarkerButton.setText("")
        # if QT_CONFIG(tooltip)
        self.removeMarkerButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Remove Marker", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.removeMarkerButton.setText("")
        # if QT_CONFIG(tooltip)
        self.previousMarkerButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Move to Previous Marker", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.previousMarkerButton.setText("")
        # if QT_CONFIG(tooltip)
        self.nextMarkerButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Move to Next Marker", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.nextMarkerButton.setText("")
        # if QT_CONFIG(tooltip)
        self.viewFullScreenButton.setToolTip(
            QCoreApplication.translate("MainWindow", "View Fullscreen (F11)", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.viewFullScreenButton.setText("")
        # if QT_CONFIG(tooltip)
        self.theatreModeButton.setToolTip(
            QCoreApplication.translate("MainWindow", "FullScreen Theatre (T)", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.theatreModeButton.setText("")
        self.findTargetFacesButton.setText(
            QCoreApplication.translate("MainWindow", "Find Faces", None)
        )
        self.clearTargetFacesButton.setText(
            QCoreApplication.translate("MainWindow", "Clear Faces", None)
        )
        self.swapfacesButton.setText(
            QCoreApplication.translate("MainWindow", "Swap Faces", None)
        )
        self.editFacesButton.setText(
            QCoreApplication.translate("MainWindow", "Edit Faces", None)
        )
        # if QT_CONFIG(tooltip)
        self.inputEmbeddingsList.setToolTip(
            QCoreApplication.translate("MainWindow", "Saved Embedding", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.saveImageButton.setText(
            QCoreApplication.translate("MainWindow", "Save Image", None)
        )
        # if QT_CONFIG(tooltip)
        self.batchImageButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Processes the currently selected face across the entire target video or image.",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.batchImageButton.setText(
            QCoreApplication.translate(
                "MainWindow",
                "Batch Process Selected Face\n(For Videos and Images)",
                None,
            )
        )
        # if QT_CONFIG(tooltip)
        self.batchallImageButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "Processes all found faces. This feature is only available for target images, not videos.",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.batchallImageButton.setText(
            QCoreApplication.translate(
                "MainWindow", "Batch Process All Faces\n(For Images only)", None
            )
        )
        self.inputEmbeddingsSearchBox.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Search Embeddings", None)
        )
        # if QT_CONFIG(tooltip)
        self.openEditorButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Open Embedding Editor", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.openEditorButton.setText(
            QCoreApplication.translate("MainWindow", "Embedding Editor", None)
        )
        # if QT_CONFIG(tooltip)
        self.openEmbeddingButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Open Embedding File", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.openEmbeddingButton.setText("")
        # if QT_CONFIG(tooltip)
        self.saveEmbeddingButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Save all embeddings to the current file", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.saveEmbeddingButton.setText("")
        # if QT_CONFIG(tooltip)
        self.saveEmbeddingAsButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Save Embedding As", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.saveEmbeddingAsButton.setText("")
        self.input_Target_DockWidget.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Target Media", None)
        )
        self.targetVideosPathLineEdit.setText("")
        self.targetVideosPathLineEdit.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Select Videos/Images Path", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonTargetVideosPath.setToolTip(
            QCoreApplication.translate("MainWindow", "Choose Target Media Folder", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonTargetVideosPath.setText("")
        self.targetVideosSearchBox.setText("")
        self.targetVideosSearchBox.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Search Videos/Images", None)
        )
        # if QT_CONFIG(tooltip)
        self.targetVideosFilterMenuButton.setToolTip(
            QCoreApplication.translate("MainWindow", "Target media filters", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.targetVideosFilterMenuButton.setText("")
        self.input_Faces_DockWidget.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Input Faces", None)
        )
        self.inputFacesPathLineEdit.setText("")
        self.inputFacesPathLineEdit.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Select Face Images Path", None)
        )
        # if QT_CONFIG(tooltip)
        self.buttonInputFacesPath.setToolTip(
            QCoreApplication.translate("MainWindow", "Choose Input Faces Folder", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.buttonInputFacesPath.setText("")
        self.inputFacesSearchBox.setPlaceholderText(
            QCoreApplication.translate("MainWindow", "Search Faces", None)
        )
        self.jobManagerDockWidget.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Job Manager", None)
        )
        self.addJobButton.setText(
            QCoreApplication.translate("MainWindow", "Save Job", None)
        )
        self.loadJobButton.setText(
            QCoreApplication.translate("MainWindow", "Load Job", None)
        )
        self.deleteJobButton.setText(
            QCoreApplication.translate("MainWindow", "Delete Job", None)
        )
        self.refreshJobListButton.setText(
            QCoreApplication.translate("MainWindow", "Refresh Job List", None)
        )
        self.buttonProcessAll.setText(
            QCoreApplication.translate("MainWindow", "Process All", None)
        )
        self.buttonProcessSelected.setText(
            QCoreApplication.translate("MainWindow", "Process Selected", None)
        )
        self.controlOptionsDockWidget.setWindowTitle(
            QCoreApplication.translate("MainWindow", "Parameters", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.face_swap_tab),
            QCoreApplication.translate("MainWindow", "Face Swap", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.face_editor_tab),
            QCoreApplication.translate("MainWindow", "Face Editor", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.common_tab),
            QCoreApplication.translate("MainWindow", "Restorers", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.denoiser_tab),
            QCoreApplication.translate("MainWindow", "Denoiser", None),
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", "Output Directory", None)
        )
        self.outputFolderButton.setText(
            QCoreApplication.translate("MainWindow", "Browse Folder", None)
        )
        self.outputOpenButton.setText(
            QCoreApplication.translate("MainWindow", "Open Folder", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.settings_tab),
            QCoreApplication.translate("MainWindow", "Settings", None),
        )
        self.labelp.setText(QCoreApplication.translate("MainWindow", "Presets", None))
        self.applyPresetButton.setText(
            QCoreApplication.translate("MainWindow", "Apply", None)
        )
        self.savePresetButton.setText(
            QCoreApplication.translate("MainWindow", "Save Current as Preset", None)
        )
        self.controlPresetButton.setText(
            QCoreApplication.translate("MainWindow", "Apply Settings", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.preset_tab),
            QCoreApplication.translate("MainWindow", "Presets", None),
        )
        self.clearMemoryButton.setText(
            QCoreApplication.translate("MainWindow", "Clear VRAM", None)
        )
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", "Edit", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", "Help", None))

    # retranslateUi
