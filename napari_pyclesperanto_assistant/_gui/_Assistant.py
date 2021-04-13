from __future__ import annotations

from pathlib import Path
from typing import Dict, TYPE_CHECKING, Tuple
from warnings import warn

from qtpy.QtWidgets import QAction, QFileDialog, QMenu, QVBoxLayout, QWidget

from .._categories import CATEGORIES, Category
from ._category_widget import make_gui_for_category
from .._export import (
    export_jython_code,
    export_jython_code_to_clipboard,
    export_notebook,
)
from ._button_grid import ButtonGrid

if TYPE_CHECKING:
    from napari.layers import Layer
    from napari.viewer import Viewer
    from napari._qt.widgets.qt_viewer_dock_widget import QtViewerDockWidget
    from magicgui.widgets import FunctionGui


class Assistant(QWidget):
    """This Gui takes a napari as parameter and infiltrates it.

    It adds some buttons for categories of _operations.
    """

    def __init__(self, napari_viewer: Viewer):
        super().__init__(napari_viewer.window.qt_viewer)
        self.viewer = napari_viewer
        napari_viewer.layers.events.removed.connect(self._on_layer_removed)
        napari_viewer.layers.selection.events.active.connect(
            self._on_active_layer_change
        )
        self._layers: Dict[Layer, Tuple[QtViewerDockWidget, FunctionGui]] = {}

        self._grid = ButtonGrid(self)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._grid)
        self._grid.addItems(CATEGORIES)
        self._grid.itemClicked.connect(self._on_item_clicked)

        # # create menu
        # self._cle_menu = QMenu("clEsperanto", self.viewer.window._qt_window)
        # self.viewer.window.plugins_menu.addMenu(self._cle_menu)
        # actions = [
        #     ("Export Jython/Python code", self._export_jython_code),
        #     (
        #         "Export Jython/Python code to clipboard",
        #         self._export_jython_code_to_clipboard,
        #     ),
        #     ("Export Jupyter Notebook", self._export_notebook),
        # ]
        # for name, cb in actions:
        #     action = QAction(name, self)
        #     action.triggered.connect(cb)
        #     self._cle_menu.addAction(action)

    def _on_active_layer_change(self, event):
        for layer, (dw, gui) in self._layers.items():
            dw.show() if event.value is layer else dw.hide()

    def _on_layer_removed(self, event):
        layer = event.value
        if layer in self._layers:
            dw = self._layers[layer][0]
            self.viewer.window.remove_dock_widget(dw)

    def _on_item_clicked(self, item):
        self._activate(CATEGORIES.get(item.text()))

    def _activate(self, category: Category):
        if not self.viewer.layers.selection.active:
            warn("Please select a layer first")
            return

        # make a new widget
        gui = make_gui_for_category(category)
        # get currently active layer (before adding dock widget)
        input_layer = self.viewer.layers.selection.active
        # add gui to the viewer
        dw = self.viewer.window.add_dock_widget(gui, area="right", name=category.name)
        # make sure the originally active layer is the input
        gui.input0.value = input_layer
        # call the function widget &
        # track the association between the layer and the gui that generated it
        self._layers[gui()] = (dw, gui)
        # turn on auto_call, and make sure that if the input changes we update
        gui._auto_call = True
        # TODO: if the input layer changes this needs to be disconnected
        input_layer.events.data.connect(lambda x: gui())

    def load_sample_data(self, fname="Lund_000500_resampled-cropped.tif"):
        data_dir = Path(__file__).parent.parent / "data"
        self.viewer.open(str(data_dir / fname))
