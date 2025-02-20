# Trait-EFO Matching Curation Tool
# Shiny app to help match traits with the most appropriate EFO term

library(shiny)
library(readr)
library(shinyWidgets)
library(DT)
library(readxl)
library(writexl)
library(dplyr)

# UI portion of the app
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      .option-btn {
        width: 100%;
        text-align: left;
        margin-bottom: 8px;
        white-space: normal;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .similarity-badge {
        min-width: 60px;
        text-align: center;
        padding: 3px 6px;
        border-radius: 10px;
        background-color: #e9ecef;
        margin-left: 10px;
      }
      .selected-option {
        border: 2px solid #28a745;
        background-color: #e8f5e9;
      }
    "))
  ),
  
  titlePanel("Trait-EFO Matching Tool"),
  
  sidebarLayout(
    sidebarPanel(width = 3,
      fileInput("file1", "Upload your CSV file", accept = ".csv"),
      
      conditionalPanel(
        condition = "output.dataLoaded",
        hr(),
        div(style = "padding: 10px; background-color: #f8f9fa; border-radius: 5px;",
            h4("Progress"),
            textOutput("progressText"),
            progressBar("progress", value = 0, display_pct = TRUE)
        ),
        hr(),
        div(
          h4("Navigation"),
          div(style = "display: flex; justify-content: space-between; margin-bottom: 15px;",
            actionButton("prev", "Previous Trait", icon = icon("arrow-left")),
            actionButton("next", "Next Trait", icon = icon("arrow-right"))
          ),
          div(style = "display: flex; align-items: center; margin-bottom: 15px;",
            div(style = "flex: 1;", numericInput("jumpToTerm", "Jump to trait #:", 1, min = 1)),
            div(style = "margin-left: 10px;", actionButton("jump", "Go", class = "btn-primary"))
          ),
          div(style = "margin-top: 15px;",
            actionButton("nextUncurated", "Next Uncurated", icon = icon("step-forward"), 
                        class = "btn-info", style = "width: 100%;")
          )
        ),
        hr(),
        downloadButton("downloadData", "Download Curated Data", class = "btn-success", style = "width: 100%;")
      )
    ),
    
    mainPanel(width = 9,
      conditionalPanel(
        condition = "!output.dataLoaded",
        div(style = "text-align: center; margin-top: 100px;",
            h3("Upload a CSV file to begin curation"),
            p("The file should contain columns for 'trait_id', 'trait', 'efo', 'efo_id', and 'similarity'")
        )
      ),
      
      conditionalPanel(
        condition = "output.dataLoaded",
        tabsetPanel(
          tabPanel("Curation Interface",
            br(),
            fluidRow(
              column(12,
                div(style = "background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;",
                    fluidRow(
                      column(9, 
                        h3(textOutput("currentTrait"), style = "margin: 0;"),
                        p(textOutput("currentTraitId"), style = "margin-top: 5px; color: #6c757d;")
                      ),
                      column(3, 
                        div(style = "text-align: right;",
                            h4("Trait", style = "margin: 0;"),
                            p(textOutput("traitNumber"), style = "margin: 0; font-size: 18px;")
                        )
                      )
                    )
                )
              )
            ),
            
            fluidRow(
              column(12,
                div(style = "padding: 15px; border: 1px solid #dee2e6; border-radius: 5px;",
                    h4("Select the most appropriate EFO term:"),
                    uiOutput("optionButtons")
                )
              )
            ),
            
            fluidRow(
              column(12,
                conditionalPanel(
                  condition = "output.hasSelection",
                  div(style = "margin-top: 20px; padding: 15px; background-color: #e8f5e9; border-radius: 5px;",
                      h4("Selected Match:"),
                      verbatimTextOutput("currentSelection")
                  )
                )
              )
            )
          ),
          
          tabPanel("Data Preview",
            br(),
            fluidRow(
              column(12,
                div(style = "margin-bottom: 20px;",
                    h4("Original Data:"),
                    DTOutput("dataTable")
                )
              )
            ),
            fluidRow(
              column(12,
                div(style = "margin-bottom: 20px;",
                    h4("Curation Progress:"),
                    DTOutput("curatedSummary")
                )
              )
            )
          ),
          
          tabPanel("Help",
            br(),
            fluidRow(
              column(12,
                div(style = "max-width: 800px; margin: 0 auto;",
                    h3("How to use this tool"),
                    p("This application helps you efficiently match traits with the most appropriate EFO (Experimental Factor Ontology) terms."),
                    
                    h4("Getting Started:"),
                    tags$ol(
                      tags$li("Upload your CSV file with the trait-EFO mapping data."),
                      tags$li("The system will display each trait with its 10 possible EFO term options."),
                      tags$li("For each trait, select the best matching EFO term by clicking on it."),
                      tags$li("Use the navigation buttons to move between traits."),
                      tags$li("Download your curated data when finished.")
                    ),
                    
                    h4("Navigation Tips:"),
                    tags$ul(
                      tags$li(strong("Previous/Next buttons:"), " Move sequentially through traits"),
                      tags$li(strong("Jump to trait:"), " Navigate directly to a specific trait number"),
                      tags$li(strong("Next Uncurated:"), " Skip to the next trait that hasn't been matched yet"),
                      tags$li(strong("Keyboard shortcuts:"), " Use number keys 1-0 to select options, arrow keys for navigation")
                    ),
                    
                    h4("Selection Tips:"),
                    tags$ul(
                      tags$li("Options are sorted by similarity score (highest first)"),
                      tags$li("Each option shows both the EFO term and its similarity score"),
                      tags$li("Selected matches are highlighted in green"),
                      tags$li("Your progress is saved automatically")
                    )
                )
              )
            )
          )
        )
      )
    )
  )
)

# Server logic
server <- function(input, output, session) {
  # Reactive values to store data and state
  values <- reactiveValues(
    data = NULL,
    uniqueTraits = NULL,
    traitOptions = NULL,
    selections = NULL,
    currentTraitIndex = 1
  )
  
  # Load data when file is uploaded
  observeEvent(input$file1, {
    req(input$file1)
    
    # Read the CSV file
    data <- read_csv(input$file1$datapath)
    
    # Store the raw data
    values$data <- data
    
    # Extract unique traits
    uniqueTraits <- data %>%
      select(trait_id, trait) %>%
      distinct()
    
    values$uniqueTraits <- uniqueTraits
    
    # Create list of options for each trait
    traitOptions <- split(data, data$trait_id)
    values$traitOptions <- traitOptions
    
    # Initialize selections dataframe
    selections <- data.frame(
      trait_id = uniqueTraits$trait_id,
      trait = uniqueTraits$trait,
      selected_efo = NA_character_,
      selected_efo_id = NA_character_,
      selected_similarity = NA_real_,
      stringsAsFactors = FALSE
    )
    values$selections <- selections
    
    # Set current trait index
    values$currentTraitIndex <- 1
  })
  
  # Check if data is loaded
  output$dataLoaded <- reactive({
    !is.null(values$data)
  })
  outputOptions(output, "dataLoaded", suspendWhenHidden = FALSE)
  
  # Helper function: Get trait ID for current index
  getCurrentTraitId <- reactive({
    req(values$uniqueTraits, values$currentTraitIndex)
    values$uniqueTraits$trait_id[values$currentTraitIndex]
  })
  
  # Helper function: Get options for current trait
  getCurrentOptions <- reactive({
    req(values$traitOptions, getCurrentTraitId())
    # Sort options by similarity
    options <- values$traitOptions[[getCurrentTraitId()]]
    options[order(options$similarity, decreasing = TRUE),]
  })
  
  # Display current trait
  output$currentTrait <- renderText({
    req(values$uniqueTraits, values$currentTraitIndex)
    values$uniqueTraits$trait[values$currentTraitIndex]
  })
  
  # Display current trait ID
  output$currentTraitId <- renderText({
    req(getCurrentTraitId())
    paste("ID:", getCurrentTraitId())
  })
  
  # Display trait number
  output$traitNumber <- renderText({
    req(values$uniqueTraits, values$currentTraitIndex)
    paste(values$currentTraitIndex, "of", nrow(values$uniqueTraits))
  })
  
  # Create buttons for EFO options
  output$optionButtons <- renderUI({
    req(getCurrentOptions())
    
    options <- getCurrentOptions()
    currentSelection <- values$selections$selected_efo_id[values$currentTraitIndex]
    
    buttonList <- lapply(1:nrow(options), function(i) {
      option <- options[i,]
      isSelected <- !is.na(currentSelection) && currentSelection == option$efo_id
      
      # Format similarity as percentage
      similarityPercent <- paste0(round(option$similarity * 100), "%")
      
      # Color code based on similarity
      similarityColor <- colorRampPalette(c("#f8d7da", "#d4edda"))(100)[round(option$similarity * 100)]
      
      actionButton(
        inputId = paste0("option_", i),
        label = div(
          div(style = "display: flex; justify-content: space-between;",
              div(
                span(strong(option$efo), style = "display: block;"),
                span(option$efo_id, style = "color: #6c757d; font-size: 0.85em;")
              ),
              span(similarityPercent, class = "similarity-badge")
          )
        ),
        class = paste("option-btn", if(isSelected) "selected-option" else ""),
        style = paste0(
          "background-color: ", similarityColor, ";", 
          if(isSelected) "border-color: #28a745;" else ""
        )
      )
    })
    
    do.call(tagList, buttonList)
  })
  
  # Handle option selection
  observe({
    req(getCurrentOptions())
    
    options <- getCurrentOptions()
    
    lapply(1:nrow(options), function(i) {
      buttonId <- paste0("option_", i)
      
      observeEvent(input[[buttonId]], {
        # Update selections data frame
        values$selections$selected_efo[values$currentTraitIndex] <- options$efo[i]
        values$selections$selected_efo_id[values$currentTraitIndex] <- options$efo_id[i]
        values$selections$selected_similarity[values$currentTraitIndex] <- options$similarity[i]
        
        # Refresh buttons to show selection
        output$hasSelection <- reactive(TRUE)
      }, ignoreInit = TRUE)
    })
  })
  
  # Check if there's a current selection
  output$hasSelection <- reactive({
    req(values$selections, values$currentTraitIndex)
    !is.na(values$selections$selected_efo[values$currentTraitIndex])
  })
  outputOptions(output, "hasSelection", suspendWhenHidden = FALSE)
  
  # Display current selection
  output$currentSelection <- renderText({
    req(values$selections, values$currentTraitIndex)
    
    if (is.na(values$selections$selected_efo[values$currentTraitIndex])) {
      return("No selection made yet")
    }
    
    selection <- values$selections[values$currentTraitIndex,]
    paste0(
      "EFO: ", selection$selected_efo, "\n",
      "ID: ", selection$selected_efo_id, "\n",
      "Similarity: ", round(selection$selected_similarity * 100, 1), "%"
    )
  })
  
  # Navigation - Previous Trait
  observeEvent(input$prev, {
    req(values$currentTraitIndex)
    if (values$currentTraitIndex > 1) {
      values$currentTraitIndex <- values$currentTraitIndex - 1
    }
  })
  
  # Navigation - Next Trait
  observeEvent(input[["next"]], {
    req(values$currentTraitIndex, values$uniqueTraits)
    if (values$currentTraitIndex < nrow(values$uniqueTraits)) {
      values$currentTraitIndex <- values$currentTraitIndex + 1
    }
  })
  
  # Jump to specific trait
  observeEvent(input$jump, {
    req(values$uniqueTraits, input$jumpToTerm)
    if (input$jumpToTerm >= 1 && input$jumpToTerm <= nrow(values$uniqueTraits)) {
      values$currentTraitIndex <- input$jumpToTerm
    }
  })
  
  # Jump to next uncurated trait
  observeEvent(input$nextUncurated, {
    req(values$selections)
    
    # Find indices of uncurated traits
    uncuratedIndices <- which(is.na(values$selections$selected_efo))
    
    # Find first uncurated trait after current index
    nextUncurated <- uncuratedIndices[uncuratedIndices > values$currentTraitIndex]
    
    # If none found after current, go to first uncurated
    if (length(nextUncurated) == 0 && length(uncuratedIndices) > 0) {
      nextUncurated <- uncuratedIndices[1]
    }
    
    # Jump to the next uncurated trait if found
    if (length(nextUncurated) > 0) {
      values$currentTraitIndex <- nextUncurated[1]
    }
  })
  
  # Update progress bar
  output$progressText <- renderText({
    req(values$selections)
    completed <- sum(!is.na(values$selections$selected_efo))
    total <- nrow(values$selections)
    paste0(completed, " of ", total, " traits curated")
  })
  
  observe({
    req(values$selections)
    completed <- sum(!is.na(values$selections$selected_efo))
    total <- nrow(values$selections)
    updateProgressBar(session, "progress", value = 100 * completed / total)
  })
  
  # Data table preview
  output$dataTable <- renderDT({
    req(values$data)
    datatable(values$data %>% select(trait_id, trait, efo, efo_id, similarity),
              options = list(pageLength = 5, scrollX = TRUE),
              rownames = FALSE)
  })
  
  # Curated summary table
  output$curatedSummary <- renderDT({
    req(values$selections)
    
    # Create summary with status column
    summary <- values$selections %>%
      mutate(status = ifelse(is.na(selected_efo), "Pending", "Completed"))
    
    datatable(summary,
              options = list(pageLength = 10, scrollX = TRUE),
              rownames = FALSE) %>%
      formatStyle(
        'status',
        backgroundColor = styleEqual(
          c('Completed', 'Pending'),
          c('#d4edda', '#f8d7da')
        )
      )
  })
  
  # Prepare data for download
  output$downloadData <- downloadHandler(
    filename = function() {
      paste0("curated_traits_", format(Sys.time(), "%Y%m%d_%H%M"), ".xlsx")
    },
    content = function(file) {
      req(values$selections)
      
      # Final output data
      write_xlsx(values$selections, file)
    }
  )
  
  # Keyboard shortcuts
  observeEvent(input$keypress, {
    req(values$currentTraitIndex, getCurrentOptions())
    
    options <- getCurrentOptions()
    
    # Number keys 1-9,0 to select options
    if (input$keypress %in% c("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")) {
      num <- as.numeric(input$keypress)
      if (num == 0) num <- 10  # Treat 0 as option 10
      
      if (num <= nrow(options)) {
        # Update selections
        values$selections$selected_efo[values$currentTraitIndex] <- options$efo[num]
        values$selections$selected_efo_id[values$currentTraitIndex] <- options$efo_id[num]
        values$selections$selected_similarity[values$currentTraitIndex] <- options$similarity[num]
        
        # Refresh buttons to show selection
        output$hasSelection <- reactive(TRUE)
      }
    }
    
    # Arrow keys for navigation
    if (input$keypress == "ArrowLeft" && values$currentTraitIndex > 1) {
      values$currentTraitIndex <- values$currentTraitIndex - 1
    }
    if (input$keypress == "ArrowRight" && 
        values$currentTraitIndex < nrow(values$uniqueTraits)) {
      values$currentTraitIndex <- values$currentTraitIndex + 1
    }
  })
}

# Add JavaScript for keyboard shortcuts
appJS <- "
$(document).on('keydown', function(e) {
  var key = e.key;
  if (/^[0-9]$/.test(key) || key == 'ArrowLeft' || key == 'ArrowRight') {
    Shiny.setInputValue('keypress', key);
    e.preventDefault();
  }
});
"

# Run the app with JS included
shinyApp(ui = tagList(tags$script(HTML(appJS)), ui), server = server)
