import streamlit as st
import numpy as np
import plotly.express as px

from spherex_api import SphereXClient


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="SPHEREx Sky Explorer",
    page_icon="🌌",
    layout="wide"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background-color: #050816;
    }

    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: white;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #b9c4df;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .card {
        background: #10172d;
        border: 1px solid #293556;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🌌 SPHEREx Sky Explorer</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Explore the infrared sky through time and search for
    moving and variable astronomical objects.
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# TARGET DATABASE
# --------------------------------------------------

TARGETS = {
    "WISE 0855": {
        "ra": 133.795129,
        "dec": -7.245147
    },

    "Barnard's Star": {
        "ra": 269.452080,
        "dec": 4.693390
    },

    "Epsilon Indi B": {
        "ra": 330.840000,
        "dec": -56.790000
    },

    "RW Aurigae": {
        "ra": 80.731000,
        "dec": 30.493000
    },

    "R Draconis": {
        "ra": 240.790000,
        "dec": 66.108000
    }
}


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("🔭 Sky Controls")

    target = st.selectbox(
        "Choose a target",
        ["Custom"] + list(TARGETS.keys())
    )

    if target != "Custom":

        ra = TARGETS[target]["ra"]
        dec = TARGETS[target]["dec"]

    else:

        ra = st.number_input(
            "Right Ascension (°)",
            min_value=0.0,
            max_value=359.999999,
            value=133.795129,
            format="%.6f"
        )

        dec = st.number_input(
            "Declination (°)",
            min_value=-90.0,
            max_value=90.0,
            value=-7.245147,
            format="%.6f"
        )

    st.divider()

    fov = st.slider(
        "Field of view",
        0.1,
        2.0,
        0.5,
        0.1
    )

    observations = st.slider(
        "Number of observations",
        2,
        8,
        5
    )

    display_mode = st.selectbox(
        "Display mode",
        [
            "Time Series",
            "Blink",
            "Difference"
        ]
    )

    st.divider()

    st.caption(
        "SPHEREx Sky Explorer"
    )


# --------------------------------------------------
# COORDINATE VALIDATION
# --------------------------------------------------

client = SphereXClient()

try:
    client.validate_coordinates(
        ra,
        dec
    )

except ValueError as error:

    st.error(str(error))
    st.stop()


ra_text, dec_text = (
    client.degrees_to_sexagesimal(
        ra,
        dec
    )
)


# --------------------------------------------------
# TARGET INFORMATION
# --------------------------------------------------

st.markdown(
    f"""
    <div class="card">

    <b>Current sky position</b><br><br>

    Right Ascension:
    {ra:.6f}° ({ra_text})<br>

    Declination:
    {dec:.6f}° ({dec_text})<br>

    Field of view:
    {fov:.1f}°

    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

if st.button(
    "🚀 Explore this region",
    type="primary",
    use_container_width=True
):

    image_list = []

    progress = st.progress(0)

    with st.spinner(
        "Loading sky observations..."
    ):

        for i in range(observations):

            image = client.get_image(
                ra=ra,
                dec=dec,
                fov=fov,
                observation=i
            )

            image_list.append(
                image
            )

            progress.progress(
                (i + 1) / observations
            )

    progress.empty()

    st.session_state.images = image_list
    st.session_state.ra = ra
    st.session_state.dec = dec
    st.session_state.fov = fov


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

if "images" in st.session_state:

    images = st.session_state.images

    st.divider()

    st.header("🛰️ Sky Observations")


    # ==============================================
    # TIME SERIES
    # ==============================================

    if display_mode == "Time Series":

        columns = st.columns(2)

        for i, image in enumerate(images):

            with columns[i % 2]:

                st.image(
                    image,
                    caption=f"Observation {i + 1}",
                    use_container_width=True
                )


    # ==============================================
    # BLINK
    # ==============================================

    elif display_mode == "Blink":

        selected = st.slider(
            "Observation",
            1,
            len(images),
            1
        )

        image = images[
            selected - 1
        ]

        st.image(
            image,
            caption=f"Observation {selected}",
            use_container_width=True
        )

        st.info(
            "Move the observation slider to look for "
            "objects that change position or brightness."
        )


    # ==============================================
    # DIFFERENCE
    # ==============================================

    elif display_mode == "Difference":

        col1, col2 = st.columns(2)

        with col1:

            first = st.selectbox(
                "First observation",
                range(len(images)),
                format_func=lambda x:
                    f"Observation {x + 1}"
            )

        with col2:

            second = st.selectbox(
                "Second observation",
                range(len(images)),
                index=1,
                format_func=lambda x:
                    f"Observation {x + 1}"
            )

        if first == second:

            st.warning(
                "Select two different observations."
            )

        else:

            difference = client.difference(
                images[first],
                images[second]
            )

            st.image(
                difference,
                caption="Difference image",
                use_container_width=True
            )


    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    st.divider()

    st.header("📊 Temporal Analysis")

    brightness = [
        float(np.mean(image))
        for image in images
    ]

    variation = [
        float(np.std(image))
        for image in images
    ]

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Observations",
            len(images)
        )

    with c2:

        st.metric(
            "Average brightness",
            f"{np.mean(brightness):.4f}"
        )

    with c3:

        st.metric(
            "Brightness variation",
            f"{np.std(brightness):.4f}"
        )


    # --------------------------------------------------
    # BRIGHTNESS CHART
    # --------------------------------------------------

    chart_data = {
        "Observation": list(
            range(1, len(images) + 1)
        ),
        "Brightness": brightness
    }

    fig = px.line(
        chart_data,
        x="Observation",
        y="Brightness",
        markers=True,
        title="Average brightness through time"
    )

    fig.update_layout(
        template="plotly_dark"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


else:

    st.info(
        "Choose a target or enter coordinates, "
        "then click 'Explore this region'."
    )


# --------------------------------------------------
# ABOUT
# --------------------------------------------------

st.divider()

st.header("About SPHEREx Sky Explorer")

st.write(
    """
    SPHEREx Sky Explorer is a public-facing prototype
    designed to make time-domain infrared astronomy easier
    to explore.

    Instead of requiring users to process astronomical
    datasets manually, this application provides a simple
    interface for comparing multiple observations of the
    same region of the sky.

    Possible discoveries include moving objects,
    variable stars, brown dwarfs, asteroids and comets.
    """
)

st.success(
    "Prototype ready — connect the data layer to real "
    "SPHEREx imagery for scientific use."
)
