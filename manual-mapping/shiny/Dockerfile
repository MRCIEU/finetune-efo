# Use the official R base image
FROM rocker/shiny

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required R packages
# RUN R -e "install.packages(c('shiny', 'DT', 'dplyr', 'readr', 'writexl', 'shinyjs', 'shinydashboard', 'shinyWidgets'), repos='https://cloud.r-project.org/')"


RUN R -e 'options( \
    repos = c(universe = "https://mrcieu.r-universe.dev/", \
        binaries = "https://p3m.dev/cran/__linux__/noble/latest", \
        CRAN = "https://cloud.r-project.org"), \
    HTTPUserAgent = sprintf( \
        "R/%s R (%s)", \
        getRversion(), \
        paste(getRversion(), \
          R.version["platform"], \
          R.version["arch"], \
          R.version["os"]))); \
    install.packages(c("shiny", "DT", "dplyr", "readr", "writexl", "shinyjs", "shinydashboard", "shinyWidgets"), dependencies = TRUE)'

# Create app directory
RUN mkdir -p /srv/shiny-server/trait-efo-matcher
WORKDIR /srv/shiny-server/trait-efo-matcher

# Copy app files
COPY app.r /srv/shiny-server/trait-efo-matcher/app.R

# Set appropriate permissions
RUN chown -R shiny:shiny /srv/shiny-server/trait-efo-matcher

# Expose port
EXPOSE 3838

# Run the Shiny app
CMD ["R", "-e", "shiny::runApp('/srv/shiny-server/trait-efo-matcher', host = '0.0.0.0', port = 3838)"]