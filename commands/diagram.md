---
name: diagram
description: Generate a professional diagram from a description
argument: Optional description of the diagram to generate
---

You are generating a diagram. Follow the generate-diagram skill exactly.

If the user provided a description: "$ARGUMENTS"

If no description was provided, ask:
> What kind of diagram would you like to create?
> - Flowchart / pipeline
> - Architecture (generic boxes + arrows)
> - Cloud/infra architecture (AWS, GCP, K8s icons)
> - ERD (entities + relationships)
> - Pyramid / stacked layers
> - Sequence diagram
> - Network / DAG
> - Block diagram
> - State machine / FSM

Then follow the generate-diagram skill's interaction protocol:
1. Classify the diagram type
2. Present library options with trade-offs
3. Ask where to save the script and SVG
4. Check prerequisites (Graphviz if needed)
5. Generate a uv-run-compatible script
6. Run it and open the SVG
7. Iterate on feedback
