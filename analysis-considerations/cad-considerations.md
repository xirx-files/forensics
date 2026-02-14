https://www.google.com/search?q=is+there+a+light+weight+open+source+viewer+for+3dm+as+alternative+to+rhino8&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQIRiPAjIHCAIQIRiPAtIBCTMzMzIwajBqN6gCALACAA&sourceid=chrome&ie=UTF-8&udm=50&fbs=ADc_l-aN0CWEZBOHjofHoaMMDiKp9lEhFAN_4ain3HSNQWw-mCdteDOdu-whizqull19J697Hd2DjFbIIkobt5MxzWRrbQzH3_BR0OTUD3HedzAmCN3eh4gdIWpbgdT4j-CUlUQzYrt88O8hmC4QDI-zJCzuennUckWqegLxB4d2UMv2V853ZU5nVZT7nDCio3gzXByIoK9D8gkH41ug3yvRx_o0Bwg4OQ&ved=2ahUKEwjA-f63pZaSAxU2cGwGHZJSArAQ0NsOegQIAxAB&aep=10&ntc=1&mstk=AUtExfDF6wsMuy6FZpz4aaUMeJ2ks3TzSDWp_vq-sOtZgrNCMHJn2IOTotKyvUAL3sZpFgWJetIQiZExt5ZSpLlWy1kbdA2pW5m2PaZ_by29eAozGmRMiwM0QndOUoj6LOutg-vL0mqS3H0vFc-4UFS-V0gGIbQeEzUbbIiyOHO5o-drRYGKGkV3r_bSx5uLh5DEmAwjVa6UqkTdmC7FYP2NUbUjYZTvICtGHpgitm-NkNJJ4F7wFwqZktCx3Bjb7sSDplTWYmeIxvZO9whsOWZ9gGq1xah43egTCgepWbz2G4TsrjxH5Eso1kn7Okz7cKg2HuM7bjESMqXFGA&csuir=1&mtid=V3RtaZnzI4uVseMPwoue2A4



    i have installed CAD assistant. i have selected an object using the mouse cursor. how do i get dimension (width, height, depth) information about it


In 2026, CAD Assistant (from Open Cascade) provides object dimensions through the Structure and Properties panels. Follow these steps to find the width, height, and depth:
1. Enable the Structure and Properties Panels
If you cannot see the panels on the side of your viewer:
Go to the 3D Viewer tab.
In the Panels group, ensure that both Structure and Properties are selected/visible. 
2. View Bounding Box Dimensions
Once an object is selected in the 3D view:
Look at the Structure panel (usually on the left). It will highlight the part or group you have selected in a tree-like hierarchy.
Look at the Properties panel (usually on the right or below the Structure panel).
Find the Box or Bounding Box section. This displays the overall dimensions of the selected object as three values: X (Width), Y (Depth), and Z (Height). 
3. Using the Measure Tool (Manual)
If you need specific distances (e.g., between two specific points or surfaces) rather than just the overall bounding box:
Navigate to the 3D Viewer tab and locate the Measure group.
Select the Distance tool.
Click a point on the first surface and then a point on the second surface.
The distance will be displayed in a floating Measure panel and directly on the model. 
4. For the Entire Model
To see the overall dimensions of the entire 3.9GB file without selecting individual parts:
On the 3D Viewer tab, go to the Visual Styles group.
Click the Bounding Box tool. This will draw a wireframe box around the entire assembly and often display its dimensions in the properties of the root node in the Structure tree. 


    is stats > Bounding Box > Range. if so how is this to be interpreted

Yes, Range under the Bounding Box (found in the Statistics/Properties panel) is exactly how you retrieve dimensions for a selected object in CAD Assistant. 
How to Interpret "Range"
The "Range" values represent the minimum and maximum coordinates of the object along the X, Y, and Z axes. To get the actual dimensions (Width, Depth, Height), you must look at the difference between these values: 
Width: The distance between X min and X max.
Depth: The distance between Y min and Y max.
Height: The distance between Z min and Z max.
Interpretation Tips for 2026
Axis-Aligned Boxes: These dimensions are "Axis-Aligned" (AABB). If your 3DM model is rotated (e.g., a chair sitting at a 45-degree angle to the grid), the "Range" will reflect a box that encompasses the rotated object, which may be larger than the object's actual physical dimensions.
Units: CAD Assistant usually inherits the units from the .3dm file (e.g., mm, cm, or inches). If the units are not explicitly shown next to the numbers, verify them in Settings > General > Units.
Accuracy: For your large 3.9GB file, CAD Assistant might use a "Fast Bounding Box" by default to save memory. For precise manufacturing dimensions, ensure "Fast Bounding Box" is unchecked in Settings > Performance. 
Recommended Workflow for Large Files
Since you are on an older laptop with a massive file:
Select the object in the Structure tree rather than the 3D viewport to avoid lag.
Navigate to the Properties/Stats area.
Manually subtract the min from the max for each axis to find your Width, Height, and Depth.


    in the bounding box section, there is min, max and range. each of these three has three number each. i dont understand


In CAD Assistant, the Bounding Box section provides the spatial limits of your object. Each entry has three numbers representing the [X, Y, Z] axes respectively.
1. How to Read the Three Values
The three values in each row correspond to the 3D coordinate system: [Number 1 (X), Number 2 (Y), Number 3 (Z)].
Min: The lowest coordinate points for each axis.
Max: The highest coordinate points for each axis.
Range: The calculated difference between Max and Min for each axis. These are your actual dimensions.
2. Finding Your Dimensions (Width, Depth, Height)
To find the size of the object you selected, look only at the Range row:
Width (X): The first number in the Range list.
Depth (Y): The second number in the Range list.
Height (Z): The third number in the Range list.
Example Interpretation:
If your Range shows: [100.0, 50.0, 200.0]
The object is 100 units wide.
The object is 50 units deep.
The object is 200 units high.
3. Why are there Min and Max?
The Min and Max rows tell you where the object is located in the 3D world (its "global coordinates"). For example, if Min X is 500 and Max X is 600, the Range X will be 100. This means the object is 100 units wide, but it is sitting 500 units away from the center of the grid.
Important Note for your 3.9GB File
Because your file is very large and you are on an older laptop, CAD Assistant may use a "Fast Bounding Box" based on the object's mesh approximation to save memory. This is usually accurate within a few percentage points, but if you need exact engineering precision, you should use the Measure Tool (the icon looks like a ruler) to click specific points on the model. 


    how can i determine the the gps and altitude (or equivalent) of the currently selected object


In 2026, CAD Assistant does not natively translate model coordinates into real-world GPS (Latitude/Longitude) or Altitude because .3dm files are typically based on a local Cartesian coordinate system (X, Y, Z).
To determine the "GPS" and "Altitude" of your object, you must interpret its relative position based on how the original model was geolocated.
1. Determining Altitude (Z-Axis)
In most architectural and engineering 3DM files, the Z-axis represents height or elevation.
How to find it: Look at the Bounding Box section again. The Min Z value usually represents the base of your object relative to the model's ground (0,0,0).
Interpretation:
If your object's Min Z is 15000 and the model uses millimeters, your object is sitting 15 meters above the model's "sea level" or "ground point."
If your file was created with real-world survey data, the Z-value is your altitude.
2. Determining GPS Location (X, Y Axes)
CAD Assistant will only show you the X and Y coordinates in the Min/Max section of the Bounding Box. To turn these into GPS coordinates, you need to know the model's Base Point.
Check the Metadata: Select the root node (the very first item) in the Structure tree. Check the Properties panel to see if there is any "User Data" or "Custom Properties" that define a "Longitude/Latitude" or a "Project Base Point."
Coordinate Offset: If the model has no metadata, you cannot get GPS coordinates without knowing the real-world location of the 0,0,0 point on the Rhino grid.
3. Using the Measure Tool for Precise Points
If you need the coordinates of a specific point on your 3.9GB model (rather than the whole object's center):
Open the Measure tool (ruler icon).
Select Distance or Point.
Click a specific vertex on your object.
The Measure Panel will display the exact [X, Y, Z] coordinates of that specific click.
Summary of Values
X / Y: Local "Easting" and "Northing." Only equivalent to GPS if the model was specifically georeferenced to a coordinate system like UTM.
Z: Your Altitude or Elevation.
Range Z: The total Height of the object itself.


    im struggling with navigation using the mouse. can you tell me to mouse controls and/keystroked for panning, titling, zooming etc


In CAD Assistant, navigation is designed to be gesture-friendly, but it can feel different from Rhino. Because you are on an older laptop, performance lag from your 3.9GB file may make the mouse feel "slippery" or unresponsive.
Here are the standard mouse and keyboard controls for 2026:
1. Basic Mouse Controls
Rotate (Tilt/Orbit): Click and drag the Left Mouse Button.
Tip: Click directly on your object before rotating; CAD Assistant uses the click-point as the "pivot" center.
Pan (Move up/down/left/right): Click and drag the Right Mouse Button.
On some Linux builds/trackpads, Middle Click (Scroll wheel click) + Drag also performs a Pan.
Zoom: Use the Mouse Wheel.
Note: The zoom follows your cursor. Point at the specific area you want to inspect to zoom "into" it.
2. Essential Keyboard Shortcuts
If the mouse is struggling with the file size, use these to reset your view:
Fit All (Zoom to Extents): Press A or F. This is vital if you lose your model in 3D space.
Front View: Press F3
Top View: Press F2
Side View: Press F4
Axonometric (3D) View: Press F1
3. Troubleshooting Navigation on Older Laptops
With a 3.9GB file, your GPU is likely struggling to redraw the frame. To make navigation smoother:
Lower the Detail: Go to Settings (Gear Icon) > Visualization. Lower the Triangulation Deviation. This makes the model look "blockier" but significantly speeds up rotation and panning.
Disable Heavy Visuals: In the 3D Viewer tab, turn off Shadows, Reflections, and Anti-aliasing.
Use the "Fit Selection": If you have an object selected in the tree, find the "Fit Selection" button (usually a magnifying glass icon with a small square) in the toolbar. This zooms the camera perfectly onto that one object, making the rotation pivot much more manageable.
Check for "Spin" mode: Ensure you haven't accidentally toggled "Flight Mode" or "First Person" if available in your version; you want "Orbit" or "Turntable" mode for standard CAD viewing.


    am able to click the mouse on a given object or space and query the X, Y & Z coordinates of that position

In CAD Assistant, you can query the specific X, Y, and Z coordinates of any point on your model by using the Measure tool.
Given your 3.9GB file, follow these steps to get coordinates with minimal lag:
1. Activating the Coordinate Query
Go to the 3D Viewer tab in the top ribbon.
Locate the Measure group and click on the Point tool (sometimes represented by a small point or coordinate icon).
Click anywhere on your object. CAD Assistant will "snap" to the nearest vertex or surface point.
A small label or Measure Panel will appear, displaying the exact X, Y, and Z coordinates of that specific mouse click.
2. Viewing Real-time Coordinates (Status Bar)
In some versions of CAD Assistant, you can enable a live coordinate tracker:
Look at the bottom status bar of the application window.
As you hover your mouse over the model (without clicking), it may display the current "Cursor Coordinates" in real-time.
Note: If this is not visible, check Settings > Interface to see if "Show Status Bar Coordinates" is toggled off.
3. Tips for Large Models (3.9GB)
Precision Snapping: Because your file is large, clicking "into space" won't give you a coordinate. You must click on the physical geometry of the model.
Tree Selection: If the model is too laggy to click accurately, select the part in the Structure tree first. Then, the Properties/Stats panel will show you the center point or bounding box coordinates for that specific component automatically.
Coordinate Units: If the numbers look extremely large or small, verify your units in Settings > General > Units. For example, a value of 1500 could mean 1500mm or 1.5 meters depending on the file's internal settings.