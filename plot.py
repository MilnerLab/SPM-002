import ctypes as ct
import os
import time

import matplotlib.pyplot as plt

#"C:\Pfad\zu\Python311-32\python.exe" -m venv .venv32   py -3.13-32 -m venv .venv
#.\.venv32\Scripts\Activate.ps1
# ---------------------------------------------------------
# DLL laden (32-bit!)
# ---------------------------------------------------------
def load_photon_spectr():
    """Lädt PhotonSpectr.dll (32-bit) aus dem Verzeichnis dieses Skripts."""
    # Prüfen, ob 32-bit Python
    if ct.sizeof(ct.c_void_p) != 4:
        raise RuntimeError(
            "PhotonSpectr.dll ist 32-bit. Bitte ein 32-bit Python verwenden "
            "(aktuell ist der Interpreter 64-bit)."
        )

    dll_name = "PhotonSpectr.dll"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.join(base_dir, dll_name)

    if not os.path.isfile(dll_path):
        raise FileNotFoundError(f"PhotonSpectr.dll nicht gefunden unter: {dll_path}")

    return ct.WinDLL(dll_path)


spm = load_photon_spectr()

# kurze Aliase
c_int = ct.c_int
c_float = ct.c_float
c_ushort = ct.c_ushort
POINTER = ct.POINTER


# ---------------------------------------------------------
# Funktionsprototypen (nur die, die wir hier brauchen)
# ---------------------------------------------------------
spm.PHO_EnumerateDevices.argtypes = []
spm.PHO_EnumerateDevices.restype = c_int

spm.PHO_Open.argtypes = [c_int]
spm.PHO_Open.restype = c_int

spm.PHO_Close.argtypes = [c_int]
spm.PHO_Close.restype = c_int

spm.PHO_GetPn.argtypes = [c_int, POINTER(c_int)]
spm.PHO_GetPn.restype = c_int

spm.PHO_GetLut.argtypes = [c_int, POINTER(c_float), c_int]
spm.PHO_GetLut.restype = c_int

spm.PHO_SetTime.argtypes = [c_int, c_float]
spm.PHO_SetTime.restype = c_int

spm.PHO_GetTime.argtypes = [c_int, POINTER(c_float)]
spm.PHO_GetTime.restype = c_int

spm.PHO_SetAverage.argtypes = [c_int, c_int]
spm.PHO_SetAverage.restype = c_int

spm.PHO_SetDs.argtypes = [c_int, c_int]
spm.PHO_SetDs.restype = c_int

spm.PHO_SetMode.argtypes = [c_int, c_int, c_int]
spm.PHO_SetMode.restype = c_int

spm.PHO_Acquire.argtypes = [c_int, c_int, c_int, POINTER(c_ushort)]
spm.PHO_Acquire.restype = c_int


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------
def init_device(dev_index=0, exposure_ms=50.0, average=1, dark_subtraction=0):
    """
    Öffnet das Spektrometer, setzt Basisparameter und gibt zurück:
    (dev_index, num_pixels, wavelength_list)
    """
    num_devices = spm.PHO_EnumerateDevices()
    if num_devices <= 0:
        raise RuntimeError("Kein Spektrometer gefunden.")

    print(f"{num_devices} Spektrometer gefunden. Verwende Gerät {dev_index}.")

    if dev_index < 0 or dev_index >= num_devices:
        raise RuntimeError(f"Ungültiger Geräteindex: {dev_index}")

    if spm.PHO_Open(dev_index) == 0:
        raise RuntimeError("PHO_Open fehlgeschlagen.")

    # Anzahl der Pixel
    num_pixels = c_int()
    if spm.PHO_GetPn(dev_index, ct.byref(num_pixels)) == 0:
        spm.PHO_Close(dev_index)
        raise RuntimeError("PHO_GetPn fehlgeschlagen.")
    npix = num_pixels.value
    print(f"CCD-Pixel: {npix}")

    # LUT für Wellenlängen
    lut = (c_float * 4)()
    if spm.PHO_GetLut(dev_index, lut, 4) == 0:
        print("Warnung: PHO_GetLut fehlgeschlagen. Verwende Pixelnummer als x-Achse.")
        wavelengths = None
    else:
        wavelengths = [
            lut[0] + lut[1] * i + lut[2] * i * i + lut[3] * i * i * i
            for i in range(npix)
        ]
        print(
            f"LUT geladen. Beispiel: Pixel 0 -> {wavelengths[0]:.2f} nm, "
            f"Pixel {npix - 1} -> {wavelengths[-1]:.2f} nm"
        )

    # Belichtungszeit
    if spm.PHO_SetTime(dev_index, float(exposure_ms)) == 0:
        print("Warnung: PHO_SetTime fehlgeschlagen.")
    else:
        t = c_float()
        if spm.PHO_GetTime(dev_index, ct.byref(t)) != 0:
            print(f"Belichtungszeit: {t.value:.1f} ms")

    # Mittelung
    if spm.PHO_SetAverage(dev_index, int(average)) == 0:
        print("Warnung: PHO_SetAverage fehlgeschlagen.")
    else:
        print(f"Averaging: {average}")

    # Dark subtraction
    if spm.PHO_SetDs(dev_index, int(dark_subtraction)) == 0:
        print("Warnung: PHO_SetDs fehlgeschlagen.")
    else:
        print(f"Dark subtraction: {dark_subtraction} (0=off, 1=on)")

    # Modus 0 = Continuous mode
    mode = 0
    scan_delay = 0
    if spm.PHO_SetMode(dev_index, mode, scan_delay) == 0:
        print("Warnung: PHO_SetMode fehlgeschlagen.")
    else:
        print("Akquisitionsmodus: 0 (Continuous)")

    return dev_index, npix, wavelengths


def live_plot(dev_index, num_pixels, wavelengths=None, update_delay=0.1):
    """
    Liest kontinuierlich Spektren und plottet sie live.
    Stop: Fenster schließen oder Strg+C im Terminal.
    """
    # Buffer für ein Spektrum
    spectrum = (c_ushort * num_pixels)()

    # Matplotlib vorbereiten
    plt.ion()
    fig, ax = plt.subplots()

    if wavelengths is not None:
        x = wavelengths
        ax.set_xlabel("Wellenlänge [nm]")
    else:
        x = list(range(num_pixels))
        ax.set_xlabel("Pixel")

    y_init = [0] * num_pixels
    (line,) = ax.plot(x, y_init)

    ax.set_ylabel("Counts")
    ax.set_title("Live-Spektrum (Strg+C im Terminal, um zu beenden)")
    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    print("Starte Live-Akquisition...")

    try:
        while plt.fignum_exists(fig.number):
            # Spektrum aufnehmen
            if spm.PHO_Acquire(dev_index, 0, num_pixels, spectrum) == 0:
                print("Fehler: PHO_Acquire fehlgeschlagen.")
                break

            # Daten in Python-Liste kopieren
            y = [spectrum[i] for i in range(num_pixels)]

            # Plot aktualisieren
            line.set_ydata(y)
            ax.relim()
            ax.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()

            time.sleep(update_delay)

    except KeyboardInterrupt:
        print("\nLive-Plot durch Benutzer abgebrochen.")

    print("Live-Plot beendet.")


# ---------------------------------------------------------
# main
# ---------------------------------------------------------
def main():
    dev_index = 0          # ggf. anpassen, falls mehrere Geräte
    exposure_ms = 50.0     # Belichtungszeit in ms
    average = 1            # Mittelungen
    dark_subtraction = 0   # 0 = aus, 1 = an

    try:
        dev_index, num_pixels, wavelengths = init_device(
            dev_index=dev_index,
            exposure_ms=exposure_ms,
            average=average,
            dark_subtraction=dark_subtraction,
        )

        live_plot(dev_index, num_pixels, wavelengths=wavelengths, update_delay=0.1)

    finally:
        # Gerät schließen, falls geöffnet
        try:
            spm.PHO_Close(dev_index)
            print("Verbindung zum Spektrometer geschlossen.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
