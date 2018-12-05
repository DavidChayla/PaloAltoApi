# PaloAltoApi

Simple python API to access PaloAlto firewall
- panorama shared
- panorama device-group
- vsys fw


Usage
```
vsys on fw cluster:
---------------
import PaloAlto
p = PaloAlto.Vsys("10.10.10.63","token","vsys1")
print(p.GetUrlCategory("test"))

panorama shared:
---------------
import PaloAlto
p = PaloAlto.Shared("10.10.10.64","token")
print(p.GetUrlCategory("test"))
p.ShowAddressName('1.1.1.1')

panorama device_group:
---------------
import PaloAlto
p = PaloAlto.DeviceGroup("10.10.10.64","token","fw1")
print(p.GetUrlCategory("test"))
```
