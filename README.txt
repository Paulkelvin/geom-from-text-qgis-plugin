# Geom From Text Optimized - QGIS Plugin

This plugin creates new cadastre parcels and beacons from CSV files with optimized performance and spatial join capabilities.

## Setup Instructions

### 1. Database Configuration
The plugin requires a PostgreSQL/PostGIS database connection. To configure:

1. Copy `config.template.ini` to `config.ini`
2. Edit `config.ini` with your database settings:
   ```ini
   [PG]
   Host=your_database_host
   Port=5432
   Database=your_database_name
   UserName=your_username
   Password=your_password
   
   [SERVICE]
   EndPoint=http://your_api_host:port/qgis-plugin-endpoint
   ```

### 2. Installation
1. Extract the plugin to your QGIS plugins directory
2. Restart QGIS
3. Enable the plugin in Plugins → Manage and Install Plugins

## Features

- ✅ Ultra-fast database connections
- ✅ Spatial joins with LGA and blocks
- ✅ Automatic parcel numbering
- ✅ Progress logging and error handling
- ✅ Optimized batch processing
- ✅ Development workflow tools

## Development

Use the provided PowerShell scripts for development:
- `quick_sync.ps1` - Quick sync to QGIS plugins directory
- `sync_plugin.ps1` - Full plugin sync
- `setup_dev_mode.ps1` - Setup development environment

## Security Note

The `config.ini` file contains sensitive database credentials and is excluded from version control. Always use your own database settings and never commit real credentials to version control.

Plugin Builder Results

Your plugin GeomFromText was created in:
    C:/QGIS/parcels/Plugin\geom_from_text

Your QGIS plugin directory is located at:
    C:/Users/GuyMagen/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins

What's Next:

  * Copy the entire directory containing your new plugin to the QGIS plugin
    directory

  * Compile the resources file using pyrcc5

  * Run the tests (``make test``)

  * Test the plugin by enabling it in the QGIS plugin manager

  * Customize it by editing the implementation file: ``geom_from_text.py``

  * Create your own custom icon, replacing the default icon.png

  * Modify your user interface by opening GeomFromText_dialog_base.ui in Qt Designer

  * You can use the Makefile to compile your Ui and resource files when
    you make changes. This requires GNU make (gmake)

For more information, see the PyQGIS Developer Cookbook at:
http://www.qgis.org/pyqgis-cookbook/index.html

(C) 2011-2018 GeoApt LLC - geoapt.com
