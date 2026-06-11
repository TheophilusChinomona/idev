# Project Map Rules

## For Split projects (FE + BE):
1. Track backend controllers, endpoints, DTOs.
2. Track frontend pages, components, API calls.
3. Map FE pages to backend endpoints.

## For Unified projects (Blazor Server, MVC):
1. Track Pages/UI components (.razor, .cshtml).
2. Track Services and Interfaces.
3. Track Domain/Entities.
4. Track Infrastructure/Data layer.
5. Map Pages to the Services they consume directly (no API layer).

## General rules:
6. Append all updates to CHANGE LOG with timestamp.
7. Never store raw source code, only summaries.
8. Only update when structural changes detected or cooldown elapsed.
