import numpy as np
import astropy.units as u
from astropy.time import Time
from scipy.interpolate import InterpolatedUnivariateSpline
from astropy.coordinates import (
    GCRS,
    ITRS,
    EarthLocation,
    CartesianRepresentation,
    get_body_barycentric_posvel,
)

from nicer.values import *

# Enable imperial units for MCC!
u.imperial.enable()


class MCC:
    """MCC
    Class to represent an MCC ephemeris for the ISS

    Initialize with an MCC ephemeris file.

    Provides interpolated lat, long for any MET time during the ephemeris valid
    interval.
    """

    def __init__(self, mccname):
        mccfile = file(mccname)
        header1 = mccfile.readline().strip()
        header2 = mccfile.readline().strip()
        self.mcc_epoch_year = float(header2.split()[0])
        self.mcc_epoch = Time(
            "{0:4.0f}-01-01T00:00:00".format(self.mcc_epoch_year),
            format="isot",
            scale="utc",
        )
        cols = np.loadtxt(mccfile, usecols=(0, 1, 2, 3), unpack=True)
        self.t = cols[0] * u.s + self.mcc_epoch
        self.met = (self.t - MET0).to(u.s).value
        self.eci_x = (cols[1] * u.imperial.foot).to(u.m)
        self.eci_y = (cols[2] * u.imperial.foot).to(u.m)
        self.eci_z = (cols[3] * u.imperial.foot).to(u.m)
        self.eci_x_interp = InterpolatedUnivariateSpline(
            self.met, self.eci_x, ext="raise"
        )
        self.eci_y_interp = InterpolatedUnivariateSpline(
            self.met, self.eci_y, ext="raise"
        )
        self.eci_z_interp = InterpolatedUnivariateSpline(
            self.met, self.eci_z, ext="raise"
        )

        # Convert ECI positions to lat, long using astropy
        cart = CartesianRepresentation(self.eci_x, self.eci_y, self.eci_z)
        eci = GCRS(cart, obstime=self.t)
        ecef = eci.transform_to(ITRS(obstime=self.t))
        self.lat = ecef.earth_location.lat
        self.lon = ecef.earth_location.lon

    def latlon(self, met):
        x = self.eci_x_interp(met)
        y = self.eci_y_interp(met)
        z = self.eci_z_interp(met)
        cart = CartesianRepresentation(x, y, z, unit=u.m)
        eci = GCRS(cart, obstime=MET0 + met * u.s)
        ecef = eci.transform_to(ITRS(obstime=MET0 + met * u.s))
        lat = ecef.earth_location.lat
        lon = ecef.earth_location.lon
        return (lat, lon)

    def plot(self):
        import matplotlib.pyplot as plt

        plt.plot(self.met, self.eci_x)
        plt.plot(self.met, self.eci_y)
        plt.plot(self.met, self.eci_z)
        plt.show()
