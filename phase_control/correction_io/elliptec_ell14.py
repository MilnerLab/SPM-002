import time
import clr
from System import Decimal
from base_lib.models import Angle, AngleUnit, Range

# === Konstanten ===
ANGLE_RANGE = Range(Angle(-90, AngleUnit.DEG), Angle(90, AngleUnit.DEG))
OUT_OF_RANGE_RELATIVE_ANGLE = Angle(45, AngleUnit.DEG)
HOME_ANGLE = Angle(0, AngleUnit.DEG)

# === DLL laden ===
clr.AddReference(r"C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll")
from Thorlabs.Elliptec.ELLO_DLL import ELLDevicePort, ELLDevices, ELLBaseDevice


class ElliptecRotator:
    def __init__(
        self,
        port: str = "COM6",
        min_address: str = "0",
        max_address: str = "F",
    ) -> None:
        self._device = None
        self._ell_devices = None

        self._delta_angle: Angle = Angle(0, AngleUnit.DEG)

        self._initialize(port, min_address, max_address)


    @property
    def delta_angle(self) -> Angle:
        return self._delta_angle

    def rotate(self, angle: Angle) -> None:
        
        if float(angle) == 0.0:
            return

        proposed_delta = Angle(self._delta_angle + angle)

        self._validate_new_delta_angle(proposed_delta)
        self._move_relative(angle)

        self._delta_angle = Angle(self._delta_angle + angle)

    def home(self) -> None:
        self._device.Home(ELLBaseDevice.DeviceDirection.Linear)
        time.sleep(1.0)
        self._delta_angle = Angle(0, AngleUnit.DEG)

    def close(self) -> None:
        try:
            ELLDevicePort.Disconnect()
        except Exception:
            pass

    # ------------------------------------------------------------------    
    # internal helpers
    # ------------------------------------------------------------------    

    def _initialize(self, port, min_address, max_address) -> None:
        print(f"Connecting to Elliptec device on {port} ...")
        ELLDevicePort.Connect(port)

        ell_devices = ELLDevices()
        devices = ell_devices.ScanAddresses(min_address, max_address)
        if not devices:
            raise RuntimeError("No Elliptec devices found on bus.")

        addressed_device = None
        for dev in devices:
            if ell_devices.Configure(dev):
                addressed_device = ell_devices.AddressedDevice(dev[0])
                break

        if addressed_device is None:
            raise RuntimeError("No configurable Elliptec device found.")

        self._ell_devices = ell_devices
        self._device = addressed_device

        device_info = self._device.DeviceInfo
        print("Connected to Elliptec device:")
        for line in device_info.Description():
            print("  ", line)

        print("Homing device...")
        self._device.Home(ELLBaseDevice.DeviceDirection.Linear)
        time.sleep(1.0)
        print("Device homed.")

        # Startzustand: delta = 0
        self._delta_angle = Angle(0, AngleUnit.DEG)

    def _move_relative(self, angle: Angle) -> None:
        d = Decimal(angle.Deg)
        self._device.MoveRelative(d)
        time.sleep(2.0)

    def _validate_new_delta_angle(self, new_delta: Angle) -> None:
        
        if ANGLE_RANGE.is_in_range(new_delta):
            return

        if new_delta > ANGLE_RANGE.max:
            correction = Angle(-OUT_OF_RANGE_RELATIVE_ANGLE)
            print("corrected max")
        elif new_delta < ANGLE_RANGE.min:
            correction = OUT_OF_RANGE_RELATIVE_ANGLE
            print("corrected min")
        else:
            correction = Angle(0)

        self._move_relative(correction)

        self._delta_angle = Angle(self._delta_angle + correction)
