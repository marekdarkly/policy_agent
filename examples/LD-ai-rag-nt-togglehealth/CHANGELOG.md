# HallucinationTracker - Changelog

## Recent Updates (Latest Release)

### 🎯 Enhanced User Experience
- **Auto-collapsing Metrics**: Chat metrics now automatically collapse when new messages are added to maintain a clean, focused interface

### 🏭 Multi-Industry Support
- **Three New Industries Added**:
  - **Mental Health**: Crisis intervention, therapy resources, medication management
  - **Healthcare**: Telemedicine, prescription services, wellness programs
  - **Investment**: Portfolio management, financial planning, market analysis
- **Dynamic Industry Loading**: Industry selection now dynamically loads based on LaunchDarkly feature flags
- **Industry-Specific Assets**: Each industry has dedicated UI components, icons, and knowledge bases

### 🔧 Technical Improvements
- **Feature Flag Integration**: 
  - AI config key standardized to `toggle-rag`
  - LaunchDarkly LLM judge key standardized to `llm-as-judge`
  - Improved flag management and monitoring
- **Enhanced Guardrail System**:
  - Case-insensitive trigger phrase detection ("ignore all previous")

