# microGUI
GUI framework for micropython.

The framework builds on top of loboris esp32 micropython port (its display module). For my specific TFT module (LOLIN TFT-2.4 V1.0.0) I had to hack the display module, since it did not work as is.
The syntax is inspired by TKinter (but simpler). 
The design is derived from material design (also much simper).

Widgets implemented so far:
* Menue
* Frame
* Label
* Button (untested)
* Slider (works nice)

