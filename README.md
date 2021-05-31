# helix_usb
helix_usb is a set of python scripts allowing for communications with Line6's HX Stomp (and maybe all other Helix products like the Helix (LT), maybe Pod Go, HX Effects and the rack version) over USB. For this, I kind of reverse engineered the protocol being send between HX Control and the HX Stomp.   

## Getting Started
git clone https://github.com/kempline/helix_usb.git 

It is recommended to create a virtual python environment. At this point only one additional library (pyusb) needs to be added:  

pip install pyusb  

Documentation: https://github.com/kempline/helix_usb/wiki

## In Action
An overview of the current features is given in 

[helix_usb - Feature Overview](https://www.youtube.com/watch?v=mRKcDVy7ZhU) 

Admitting that those features seem useless on their own, here's another video showing a typical use-case of helix_usb.

[Combining helix_usb with a Line6 FBV3](https://www.youtube.com/watch?v=1Qndof3cb20)

