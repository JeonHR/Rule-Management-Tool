# Rule Management Tool
PyQt5 Configuration Manager for Product/Version/Rule 

#### Purpose
- Reduces equipment changeover time to boost utilization and save engineering effort.
<img width="595" height="363" alt="image" src="https://github.com/user-attachments/assets/c57d1fce-4369-46b9-827a-b3b71dd829f9" />


#### Key Features
- Role separation between Engineer and Operator to eliminate confusion and reduce errors
- Two specialized change types:
  - TXT_PATH_CHANGE – for text/path configuration updates
  - FILE_CHANGE – for full file replacement or updates
- Per-rule delete capability for safe and selective rule removal


#### Application Simulation

  

#### Knowledge
- Role-based UI Visibility Control
  - Dynamically shows or hides engineering-specific controls (on_mode_change)
- Effective utilization of dictionaries enables straightforward implementation
  - Utilized dictionaries to implement storage, retrieval, and deletion operations
- Proactive Prevention of Side Effects in UI Operations
  - Anticipated and prevented side effects of button operations to ensure stable and predictable system behavior
