import io
import requests
import numpy as np

from PIL import Image
from astropy.coordinates import SkyCoord
import astropy.units as u


class SphereXClient:
    def __init__(self, service_url=None):
        self.service_url = service_url

    def validate_coordinates(self, ra, dec):
        if not 0 <= ra < 360:
            raise ValueError("RA must be between 0 and 360 degrees.")

        if not -90 <= dec <= 90:
            raise ValueError("Declination must be between -90 and +90 degrees.")

    def convert_coordinates(self, ra, dec):
        self.validate_coordinates(ra, dec)

        return SkyCoord(
            ra=ra * u.degree,
            dec=dec * u.degree,
            frame="icrs"
        )

    def sexagesimal_to_degrees(self, ra, dec):
        coordinate = SkyCoord(
            ra,
            dec,
            frame="icrs"
        )

        return coordinate.ra.degree, coordinate.dec.degree

    def degrees_to_sexagesimal(self, ra, dec):
        coordinate = SkyCoord(
            ra=ra * u.degree,
            dec=dec * u.degree,
            frame="icrs"
        )

        return (
            coordinate.ra.to_string(
                unit=u.hour,
                sep=":",
                precision=2
            ),
            coordinate.dec.to_string(
                unit=u.degree,
                sep=":",
                precision=2,
                alwayssign=True
            )
        )

    def get_image(
        self,
        ra,
        dec,
        fov=0.5,
        band=1,
        observation=0
    ):
        self.validate_coordinates(ra, dec)

        if self.service_url:
            try:
                return self._download_image(
                    ra,
                    dec,
                    fov,
                    band,
                    observation
                )
            except Exception:
                pass

        return self._demo_image(
            ra,
            dec,
            fov,
            observation
        )

    def _download_image(
        self,
        ra,
        dec,
        fov,
        band,
        observation
    ):
        params = {
            "ra": ra,
            "dec": dec,
            "fov": fov,
            "band": band,
            "observation": observation
        }

        response = requests.get(
            self.service_url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        image = Image.open(
            io.BytesIO(response.content)
        )

        return np.asarray(image)

    def _demo_image(
        self,
        ra,
        dec,
        fov,
        observation
    ):
        """
        Demo infrared sky image.

        This is used until a real SPHEREx imagery
        endpoint is connected.
        """

        size = 512

        seed = int(
            abs(
                ra * 10000 +
                dec * 1000 +
                observation * 99991
            )
        ) % (2**32 - 1)

        rng = np.random.default_rng(seed)

        image = rng.normal(
            0.03,
            0.01,
            (size, size)
        )

        y, x = np.mgrid[
            0:size,
            0:size
        ]

        # Add simulated astronomical sources
        for _ in range(45):

            cx = rng.uniform(15, size - 15)
            cy = rng.uniform(15, size - 15)

            brightness = rng.uniform(
                0.15,
                1.0
            )

            # Simulated motion between observations
            cx += observation * rng.uniform(
                -4,
                4
            )

            cy += observation * rng.uniform(
                -2,
                2
            )

            sigma = rng.uniform(
                0.8,
                3.0
            )

            source = brightness * np.exp(
                -(
                    (x - cx) ** 2 +
                    (y - cy) ** 2
                ) /
                (2 * sigma ** 2)
            )

            image += source

        # Simulated extended object
        galaxy_x = size * 0.65
        galaxy_y = size * 0.35

        galaxy = 0.12 * np.exp(
            -(
                ((x - galaxy_x) / 40) ** 2 +
                ((y - galaxy_y) / 20) ** 2
            )
        )

        image += galaxy

        return self.normalize(image)

    @staticmethod
    def normalize(image):
        image = image.astype(float)

        low = np.percentile(
            image,
            1
        )

        high = np.percentile(
            image,
            99
        )

        if high == low:
            return np.zeros_like(image)

        image = (
            image - low
        ) / (
            high - low
        )

        return np.clip(
            image,
            0,
            1
        )

    @staticmethod
    def difference(image1, image2):
        difference = (
            image2.astype(float)
            -
            image1.astype(float)
        )

        return SphereXClient.normalize(
            np.abs(difference)
        )

    @staticmethod
    def stack(images):
        if not images:
            raise ValueError(
                "No images provided."
            )

        return SphereXClient.normalize(
            np.mean(
                np.asarray(images),
                axis=0
            )
        )
