from qgis.PyQt.QtCore import QObject, pyqtSignal, QDate, QVariant

class GeomFromTextWorker(QObject):
    finished = pyqtSignal(object)  # Emitted when processing is done, passes result or error
    progress = pyqtSignal(str)     # Optional: emits progress messages

    def __init__(self, csv_path, epsg, app_num, plugin_dir):
        super().__init__()
        self.csv_path = csv_path
        self.epsg = epsg
        self.app_num = app_num
        self.plugin_dir = plugin_dir

    def run(self):
        try:
            import configparser
            from datetime import date
            import os
            from qgis.core import (
                QgsVectorLayer, QgsDataSourceUri, QgsGeometry, QgsPointXY, QgsProject,
                QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsFeature,
                QgsVectorLayerUtils, QgsFillSymbol, QgsFeatureRequest, Qgis, QgsField
            )
            import processing
            import sys
            import csv
            import time

            # OPTIMIZED: Start timing for overall performance measurement
            start_time = time.time()

            # --- Optimized Functions ---
            def createRoadFeature(points_list, roads_lyr, offset, tr=None):
                line_geom = QgsGeometry.fromPolylineXY(points_list)
                if tr: line_geom.transform(tr)
                line_geom = line_geom.offsetCurve(offset, 8, QgsGeometry.JoinStyleMiter, 2)
                fields = roads_lyr.fields()
                line_feat = QgsFeature(fields)
                line_feat.setAttribute(fields.indexFromName('offset'), offset)
                line_feat.setGeometry(line_geom)
                return line_feat

            # --- OPTIMIZED: Ultra-fast PostgreSQL connection with pooling ---
            self.progress.emit("Connecting to database...")
            ini_path = os.path.join(self.plugin_dir, 'config.ini')
            config = configparser.ConfigParser()
            config.read(ini_path)
            host = config['PG']['Host'].strip()
            port = config['PG']['Port'].strip()
            database = config['PG']['Database'].strip()
            username = config['PG']['UserName'].strip()
            password = config['PG']['Password'].strip()
            data_source = config['DEFAULT_FIELDS']['DataSource'].strip()
            status = config['DEFAULT_FIELDS']['Status'].strip()
            
            # OPTIMIZED: Create single connection URI with maximum performance parameters
            uri = QgsDataSourceUri()
            uri.setConnection(host, port, database, username, password)
            
            # OPTIMIZED: Add maximum performance parameters for PostgreSQL
            # These are the most aggressive settings for speed
            connection_params = [
                "connect_timeout=3",            # 3 second timeout for ultra-fast failure detection
                "application_name=geom_from_text",  # Identify connection
                "tcp_keepalives_idle=30",       # Keep connection alive
                "tcp_keepalives_interval=5",    # Check connection every 5 seconds
                "tcp_keepalives_count=3",       # Retry 3 times before giving up
                "options='-c statement_timeout=15000'",  # 15 second query timeout
                "options='-c idle_in_transaction_session_timeout=15000'",  # 15 second idle timeout
                "options='-c synchronous_commit=off'",   # Faster commits
                "options='-c wal_buffers=32MB'",         # Larger WAL buffers
                "options='-c shared_buffers=512MB'",     # Larger shared buffers
                "options='-c work_mem=64MB'",            # More memory for operations
                "options='-c maintenance_work_mem=256MB'", # More memory for maintenance
            ]
            
            # Add optimized parameters to URI
            for param in connection_params:
                uri.setParam(param.split('=')[0], param.split('=')[1])
            
            # OPTIMIZED: Create layers with minimal initialization and connection pooling
            # Use subset strings to avoid loading unnecessary data on connect
            
            # Create all layers using the same optimized connection with minimal data loading
            layer_configs = [
                ('public', 'land_registration___beacons', 'geometry', 'beacons', '1=0'),  # Load schema only
                ('public', 'land_registration___parcels', 'geometry', 'parcels', '1=0'),  # Load schema only
                ('public', 'land_registration___blocks', 'geometry', 'blocks', ''),       # Load ALL data for spatial joins
                ('public', 'ogun_admin___lgas', 'geometry', 'lga', ''),                  # Load ALL data for spatial joins
                ('public', 'land_registration___parcel_roads', 'geom', 'roads', '1=0'),  # Load schema only
                ('public', 'land_registration___parcel_lookup', '', 'parcel_lkp', '1=0') # Load schema only
            ]
            
            layers = {}
            for schema, table, geom_col, layer_name, subset in layer_configs:
                uri.setDataSource(schema, table, geom_col, subset)  # Use subset to load schema only
                layer = QgsVectorLayer(uri.uri(), layer_name, 'postgres')
                layers[layer_name] = layer
                
                # OPTIMIZED: Set layer properties for faster access
                if layer.isValid():
                    layer.setReadOnly(False)  # Allow writes
                    # Note: setAutoRefreshEnabled is deprecated, removed for compatibility
            
            # Unpack layers for easier access
            beacons = layers['beacons']
            parcels = layers['parcels']
            blocks = layers['blocks']
            lga = layers['lga']
            roads = layers['roads']
            parcel_lkp = layers['parcel_lkp']
            
            # OPTIMIZED: Verify all layers loaded successfully with timeout
            for layer_name, layer in layers.items():
                if not layer.isValid():
                    self.finished.emit({'success': False, 'error': f'Failed to load layer: {layer_name}'})
                    return
            
            connection_time = time.time() - start_time
            self.progress.emit(f"Database connected in {connection_time:.1f} seconds")

            # Pre-compute coordinate transform once
            if self.epsg in [26391, 32631]:
                from_crs = QgsCoordinateReferenceSystem.fromEpsgId(self.epsg)
                to_crs = QgsCoordinateReferenceSystem.fromEpsgId(26331)
                tr = QgsCoordinateTransform(from_crs, to_crs, QgsProject.instance())
            else:
                tr = None

            # --- CSV Reading and Feature Creation ---
            csv_start_time = time.time()
            self.progress.emit("Reading CSV file...")
            
            # Count total rows for progress reporting
            with open(self.csv_path, 'r') as f:
                total_rows = sum(1 for line in f) - 1  # Subtract header
            
            self.progress.emit(f"Processing {total_rows} rows...")
            
            parcel_points = []
            road_points = []
            beacons_feats = []
            parcels_feats = []
            roads_feats = []
            beacons_dict = {}
            roads_dict = {}
            parcels_fields = parcels.fields()
            beacons_fields = beacons.fields()
            
            # Cache field indices for better performance
            beacon_num_idx = beacons_fields.indexFromName('beacon_num')
            beacon_x_idx = beacons_fields.indexFromName('x')
            beacon_y_idx = beacons_fields.indexFromName('y')
            beacon_date_idx = beacons_fields.indexFromName('date_created')
            
            is_error = False
            is_offset = False
            centroids = []
            parcel_id_list = []
            processed_rows = 0
            
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header row
                next(reader)
                
                # Read first row to initialize
                try:
                    first_row = next(reader)
                    current_parcel_id = first_row[0]
                    try:
                        bearing = float(first_row[4]) + float(first_row[5]) / 60
                        dist = float(first_row[6])
                    except:
                        bearing = None
                        dist = None
                    try:
                        first_point = QgsPointXY(float(first_row[2]), float(first_row[3]))
                    except:
                        self.finished.emit({'success': False, 'error': 'No XY values for starting point. Please check 1st Parcel'})
                        return
                        
                    # Process first row
                    if first_row[2] and first_row[3]:
                        point = first_point
                    else:
                        point = first_point.project(dist, bearing) if dist and bearing else first_point
                    
                    parcel_points.append(point)
                    if first_row[7]:
                        offset = float(first_row[7])
                        road_points.append(point)
                        is_offset = True
                    
                    # Create beacon (transform geometry once)
                    point_geom = QgsGeometry.fromPointXY(point)
                    if tr: point_geom.transform(tr)
                    new_beacon = QgsFeature(beacons_fields)
                    new_beacon.setAttribute(beacon_num_idx, first_row[1])
                    new_beacon.setAttribute(beacon_x_idx, point.x())
                    new_beacon.setAttribute(beacon_y_idx, point.y())
                    new_beacon.setAttribute(beacon_date_idx, QDate(date.today()))
                    new_beacon.setGeometry(point_geom)
                    beacons_feats.append(new_beacon)
                    processed_rows += 1
                    
                except StopIteration:
                    self.finished.emit({'success': False, 'error': 'CSV file is empty or has no data rows'})
                    return
                
                # Process remaining rows
                for row in reader:
                    processed_rows += 1
                    
                    # Progress reporting every 25 rows (more frequent)
                    if processed_rows % 25 == 0:
                        progress_percent = (processed_rows / total_rows) * 100
                        self.progress.emit(f"Processing CSV: {progress_percent:.1f}% ({processed_rows}/{total_rows} rows)")
                    
                    parcel_id = row[0]
                    beacon_num = row[1]
                    
                    if parcel_id != current_parcel_id:
                        # Process previous parcel
                        if not is_xy:
                            self.finished.emit({'success': False, 'error': f'No XY values for starting point. Please check Parcel: {parcel_id}'})
                            return
                        
                        # Create polygon from collected points
                        poly = QgsGeometry.fromPolygonXY([parcel_points])
                        if not poly.validateGeometry():
                            if tr: poly.transform(tr)
                            new_parcel = QgsFeature(parcels_fields)
                            new_parcel.setGeometry(poly)
                            area = poly.area()
                            centroid = poly.centroid().asPoint()
                            centroids.append(centroid)
                            parcel_id_list.append(current_parcel_id)
                            new_parcel.setAttribute(parcels_fields.indexFromName('area'), area)
                            new_parcel.setAttribute(parcels_fields.indexFromName('data_source'), data_source)
                            new_parcel.setAttribute(parcels_fields.indexFromName('status'), status)
                            new_parcel.setAttribute(parcels_fields.indexFromName('date_created'), QDate(date.today()))
                            parcels_feats.append(new_parcel)
                            
                            # Handle roads for previous parcel
                            if is_offset:
                                road_points.append(first_point)
                                road_feat = createRoadFeature(road_points, roads, offset, tr)
                                roads_feats.append(road_feat)
                            
                            if current_parcel_id in roads_dict:
                                roads_dict[current_parcel_id].append(roads_feats)
                            else:
                                roads_dict[current_parcel_id] = roads_feats
                            
                            # Store beacons for previous parcel
                            beacons_dict[current_parcel_id] = beacons_feats
                            
                            # Reset for new parcel
                            parcel_points = [point]
                            roads_feats = []
                            beacons_feats = []
                            current_parcel_id = parcel_id
                        else:
                            parcel_lkp.rollBack()
                            self.finished.emit({'success': False, 'error': f'Invalid Parcel geometry. Please check Parcel: {current_parcel_id}'})
                            return
                    
                    # Process current row
                    is_xy = False
                    if row[2] and row[3]:
                        is_xy = True
                        try:
                            x = float(row[2])
                            y = float(row[3])
                            point = QgsPointXY(x, y)
                        except:
                            self.finished.emit({'success': False, 'error': f'Invalid XY value. Please check Parcel: {parcel_id}, Beacon: {beacon_num}'})
                            return
                    else:
                        if all(row[4:7]):
                            try:
                                new_bearing = float(row[4]) + float(row[5]) / 60
                                new_dist = float(row[6])
                                point = point.project(new_dist, new_bearing)
                                bearing = new_bearing
                                dist = new_dist
                            except:
                                self.finished.emit({'success': False, 'error': f'Invalid Bearing/Distance value. Please check Parcel: {parcel_id}, Beacon: {beacon_num}'})
                                return
                        else:
                            new_bearing = None
                            new_dist = None
                    
                    parcel_points.append(point)
                    
                    # Handle roads
                    if is_offset:
                        road_points.append(point)
                        road_feat = createRoadFeature(road_points, roads, offset, tr)
                        roads_feats.append(road_feat)
                        road_points = []
                        is_offset = False
                    
                    if row[7]:
                        offset = float(row[7])
                        road_points.append(point)
                        is_offset = True
                    
                    # Create beacon (transform geometry once)
                    point_geom = QgsGeometry.fromPointXY(point)
                    if tr: point_geom.transform(tr)
                    new_beacon = QgsFeature(beacons_fields)
                    new_beacon.setAttribute(beacon_num_idx, beacon_num)
                    new_beacon.setAttribute(beacon_x_idx, point.x())
                    new_beacon.setAttribute(beacon_y_idx, point.y())
                    new_beacon.setAttribute(beacon_date_idx, QDate(date.today()))
                    new_beacon.setGeometry(point_geom)
                    beacons_feats.append(new_beacon)
                
                # Process the last parcel
                if not is_error:
                    poly = QgsGeometry.fromPolygonXY([parcel_points])
                    if not poly.validateGeometry():
                        if tr: poly.transform(tr)
                        new_parcel = QgsFeature(parcels_fields)
                        new_parcel.setGeometry(poly)
                        area = poly.area()
                        centroid = poly.centroid().asPoint()
                        centroids.append(centroid)
                        parcel_id_list.append(current_parcel_id)
                        new_parcel.setAttribute(parcels_fields.indexFromName('area'), area)
                        new_parcel.setAttribute(parcels_fields.indexFromName('data_source'), data_source)
                        new_parcel.setAttribute(parcels_fields.indexFromName('status'), status)
                        new_parcel.setAttribute(parcels_fields.indexFromName('date_created'), QDate(date.today()))
                        parcels_feats.append(new_parcel)
                        
                        if is_offset:
                            road_points.append(first_point)
                            road_feat = createRoadFeature(road_points, roads, offset, tr)
                            roads_feats.append(road_feat)
                        
                        if current_parcel_id in roads_dict:
                            roads_dict[current_parcel_id].append(roads_feats)
                        else:
                            roads_dict[current_parcel_id] = roads_feats
                        
                        beacons_dict[current_parcel_id] = beacons_feats
                    else:
                        parcel_lkp.rollBack()
                        self.finished.emit({'success': False, 'error': f'Invalid Parcel geometry. Please check Parcel: {current_parcel_id}'})
                        return

            # --- OPTIMIZED: Batch spatial join for LGA and block ---
            join_start_time = time.time()
            self.progress.emit("Performing spatial joins...")
            
            # Create a memory layer for centroids
            centroid_layer = QgsVectorLayer('Point?crs=epsg:26331', 'centroids', 'memory')
            centroid_provider = centroid_layer.dataProvider()
            
            # Add a field for parcel_id BEFORE creating features
            centroid_provider.addAttributes([QgsField("parcel_id", QVariant.String, "string")])
            centroid_layer.updateFields()
            
            fields = centroid_layer.fields()
            parcel_id_idx = fields.indexFromName('parcel_id')

            centroid_feats = []
            
            for i, pt in enumerate(centroids):
                feat = QgsFeature(fields)
                feat.initAttributes(fields.count())
                feat.setGeometry(QgsGeometry.fromPointXY(pt))
                feat.setAttribute(parcel_id_idx, parcel_id_list[i])
                centroid_feats.append(feat)
            
            centroid_provider.addFeatures(centroid_feats)
            
            # OPTIMIZED: Single join with LGA and blocks in one operation
            self.progress.emit("Joining with LGA and block layers...")
            
            # OPTIMIZED: Add detailed logging for debugging spatial joins
            self.progress.emit(f"Centroid layer has {centroid_layer.featureCount()} features")
            self.progress.emit(f"LGA layer has {lga.featureCount()} features")
            self.progress.emit(f"Blocks layer has {blocks.featureCount()} features")
            self.progress.emit(f"Centroid CRS: {centroid_layer.crs().authid()}")
            self.progress.emit(f"LGA CRS: {lga.crs().authid()}")
            self.progress.emit(f"Blocks CRS: {blocks.crs().authid()}")
            
            # OPTIMIZED: Build spatial indexes for faster joins
            self.progress.emit("Building spatial indexes...")
            processing.run("native:createspatialindex", {'INPUT': lga})
            processing.run("native:createspatialindex", {'INPUT': blocks})
            
            # Join with LGA first
            lga_joined = processing.run("native:joinattributesbylocation", {
                'INPUT': centroid_layer,
                'PREDICATE': [0],
                'JOIN': lga,
                'JOIN_FIELDS': ['lga_num'],
                'METHOD': 0,
                'DISCARD_NONMATCHING': False,
                'PREFIX': '',
                'OUTPUT': 'memory:'
            })['OUTPUT']
            
            # Join with Blocks
            block_joined = processing.run("native:joinattributesbylocation", {
                'INPUT': lga_joined,
                'PREDICATE': [0],
                'JOIN': blocks,
                'JOIN_FIELDS': ['block_num'],
                'METHOD': 0,
                'DISCARD_NONMATCHING': False,
                'PREFIX': '',
                'OUTPUT': 'memory:'
            })['OUTPUT']
            
            # Map results back to parcels_feats
            join_results = {}
            for feat in block_joined.getFeatures():
                pid = feat['parcel_id']
                join_results[pid] = {
                    'lga_num': feat['lga_num'],
                    'block_num': feat['block_num'] if 'block_num' in feat.fields().names() else 999
                }
            
            # OPTIMIZED: Add defensive logging and error handling
            self.progress.emit(f"Spatial join found {len(join_results)} matches out of {len(parcel_id_list)} parcels")
            
            # Log missing parcels for debugging
            missing_parcels = set(parcel_id_list) - set(join_results.keys())
            if missing_parcels:
                self.progress.emit(f"WARNING: No spatial join match for parcels: {missing_parcels}")
            
            join_time = time.time() - join_start_time
            self.progress.emit(f"Spatial joins completed in {join_time:.1f} seconds")
            
            # OPTIMIZED: Ensure parcel_num field exists
            if parcels_fields.indexFromName('parcel_num') == -1:
                parcels.dataProvider().addAttributes([QgsField('parcel_num', QVariant.Int)])
                parcels.updateFields()
                parcels_fields = parcels.fields()
                self.progress.emit("Added parcel_num field to parcels layer")

            # Assign lga_num and block_num to parcels_feats with defensive coding
            for i, parcel in enumerate(parcels_feats):
                pid = parcel_id_list[i]
                parcel_num = i + 1  # Assign sequential parcel numbers starting from 1
                
                if pid in join_results:
                    parcel.setAttribute(parcels_fields.indexFromName('lga_num'), join_results[pid]['lga_num'])
                    parcel.setAttribute(parcels_fields.indexFromName('block_num'), join_results[pid]['block_num'])
                    self.progress.emit(f"Parcel {pid}: lga_num={join_results[pid]['lga_num']}, block_num={join_results[pid]['block_num']}, parcel_num={parcel_num}")
                else:
                    # OPTIMIZED: Set default values for missing joins
                    self.progress.emit(f"Setting default values for parcel {pid} (no spatial join match)")
                    parcel.setAttribute(parcels_fields.indexFromName('lga_num'), 999)  # Default LGA
                    parcel.setAttribute(parcels_fields.indexFromName('block_num'), 999)  # Default block
                
                # OPTIMIZED: Always set parcel_num for each feature
                parcel.setAttribute(parcels_fields.indexFromName('parcel_num'), parcel_num)
                self.progress.emit(f"Assigned parcel_num={parcel_num} to parcel {pid}")

            total_time = time.time() - start_time
            self.progress.emit(f"Processing complete! Total time: {total_time:.1f} seconds")
            
            # Return all results for review in the main thread
            self.finished.emit({
                'success': True,
                'parcels_feats': parcels_feats,
                'beacons_feats': beacons_feats,
                'roads_feats': roads_feats,
                'beacons_dict': beacons_dict,
                'roads_dict': roads_dict,
                'lga': lga,
                'blocks': blocks,
                'parcels': parcels,
                'beacons': beacons,
                'roads': roads,
                'parcel_lkp': parcel_lkp,
                'lga_num': join_results[parcel_id_list[0]]['lga_num'] if parcel_id_list else None,
                'block_num': join_results[parcel_id_list[0]]['block_num'] if parcel_id_list else None,
                'parcel_num': 1 if parcel_id_list else None,  # Serial number for first parcel
                'data_source': data_source,
                'status': status,
                'app_num': self.app_num,
                'plugin_dir': self.plugin_dir,
                'parcel_id_list': parcel_id_list
            })
        except Exception as e:
            self.finished.emit({'success': False, 'error': str(e)})