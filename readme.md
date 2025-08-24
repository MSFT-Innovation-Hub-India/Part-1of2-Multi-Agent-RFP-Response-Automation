## [Part 1 of 2] Multi Agent RFP Response Automation
Multi Agent System representing the Proposal Management System
This is meant to be used in tandem with another project, Marketing and Communications Assistant, that is hosted in another GitHub Repo  - https://github.com/MSFT-Innovation-Hub-India/corp-comms-asst

This is based on autogen, and heavily uses the Azure Open AI Assistants API
A user sends a request to create an RFP Response for a specific RFP. The request is sent to the Marketing and Communications Assistant, which then sends a request to this project to create the RFP Response. This project then creates the RFP Response and sends it to the Marketing and Communications Assistant, to populate the Customer Stories and Customer testimonials, which then sends it back to the user.

The final RFP Response gets uploaded to https://oai.azure.com/resource/datafile?wsid=/subscriptions/bc2e2415-164d-45a5-9a4a-29d9264a343e/resourceGroups/aoai-rg/providers/Microsoft.CognitiveServices/accounts/oai-sansri-eastus2&tid=16b3c013-d300-468d-ac64-7eda0820b6d3 as a Microsoft Word Document
