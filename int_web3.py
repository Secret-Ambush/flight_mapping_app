import streamlit as st
import polars as pl
import pandas as pd
import folium
from streamlit_folium import folium_static
# from folium import plugins
from PIL import Image  

img = Image.open("emirates_logo.png")

header = st.container()
data = st.container()
features = st.container()

with header:
    
    text_col,image_col = st.columns((5.5,1))
    
    with text_col:
        st.title("Welcome to our Flight Analysis Visualization")
        st.markdown("This webapp demonstrates all the **LEG_SCHEDULES** on the worldmap.")
    
    with image_col:
        st.write("##")
        st.image(img,width = 100)

with data:
    st.header("DATASET")
    st.markdown("Using the **dataset** we formed from the **Intern Exercies** *(attatached for reference)*")

    left_col,right_col = st.columns((5,1))

    with left_col:
        dtypes = {'flight_number': str}
        traffic_control = pl.read_csv('traffic_control.csv', infer_schema_length=10000, dtypes=dtypes, ignore_errors=True)

        st.dataframe(traffic_control.tail(50),height=510)

        st.write("##")
        
        st.subheader("SEG_DISTANCE distribution")
        st.write("##")
        seg_distance = pd.DataFrame(traffic_control['seg_distance'].unique_counts())
        st.bar_chart(seg_distance)
        st.write("##")

    with right_col:
        numbers = """
        1. *airline_code*
        2. *flight_number*
        3. *leg_sequence_start*
        4. *leg_sequence_end*
        5. *aircraft_type*
        6. *seg_origin*
        7. *seg_dest*
        8. *dept_date*
        9. *arr_date*
        10. *departure_gmt*
        11. *arrival_gmt*
        12. *routing*
        13. *travel_time*
        14. *conn_time*
        15. *seg_distance*
        16. *traffic_restriction*
        17. *circuity*
        """   
        st.markdown(numbers)

with features:
    st.header("Features we created")
    st.markdown("Here you get to choose the hyperparameters and see the schedules available")
    
    option = st.radio("Filter based on:", ["Number of legs", "Origin"])
    sel_col, disp_col = st.columns((1, 3))

    coordinates = pl.read_csv('coordinates.csv', infer_schema_length=10000, ignore_errors=True)
    
    if option == "Number of legs":
        with sel_col:
            st.write("##")
            no_legs = st.slider("Number of legs", min_value=1, max_value=10, value=1, step=1)
            
            # drop down for airline code
            airline_code_data = pd.DataFrame(traffic_control['airline_code'].unique())
            airline_code_data = airline_code_data.sort_values(0, ascending=True)

            airline_code_inp = sel_col.selectbox("Give the required airline code", options=airline_code_data)

            sel = sel_col.selectbox("Give the requirement", options=['Longest Route','Most circuitous'])

        with disp_col:
            st.write("##")
            # Load the CSV files
            coordinates_df = pd.read_csv('coordinates.csv',low_memory=False)
            traffic_df = pd.read_csv('traffic_control.csv',low_memory=False)

            ## Take user inputs
            airline_code = airline_code_inp

            # Ask the user for the desired route type
            route_type = sel

            # Filter data based on user inputs
            filtered_df = traffic_df[
            (traffic_df['airline_code'] == airline_code) &
            (traffic_df['leg_sequence_end'] - traffic_df['leg_sequence_start'] == (no_legs - 1) )]
            
            # Check if there are any matching routes
            if filtered_df.empty:
                st.warning("No routes found for the given inputs.")
                exit()

            # Check the desired route type
            if route_type == 'Longest Route':
                # Find the longest route
                longest_route = filtered_df.loc[filtered_df['seg_distance'].idxmax()]
                routing = longest_route['routing']
                
                #to display the travel time in minutes and seg_dist
                time_mins = str(longest_route['travel_time'])
                seg_dist = str(round(longest_route['seg_distance'],3))
                st.markdown("The segment distance (kilometers): "+seg_dist)
                st.markdown("The Travel Time (minutes): "+time_mins)
                
            elif route_type == 'Most circuitous':
                # Find the route with the highest circuity value
                highest_circuity_route = filtered_df.loc[filtered_df['circuity'].idxmax()]
                routing = highest_circuity_route['routing']
                
                #to display the circuity value and the seg_dist
                cir = str(highest_circuity_route['circuity'])
                seg_dist = str(round(highest_circuity_route['seg_distance'],3))
                st.markdown("The segment distance (kilometers) is: "+seg_dist)
                st.markdown("The Circuity value is: "+cir)
            else:
                print("Invalid route type.")
                exit()

            # Extract airport codes from the routing column
            airport_codes = routing.split('-')

            # Get coordinates for each airport code
            coordinates = coordinates_df[coordinates_df['airport_code'].isin(airport_codes)][['latitude', 'longitude']]

            # Create a Folium map centered at the first airport
            map = folium.Map(location=[coordinates.iloc[0]['latitude'], coordinates.iloc[0]['longitude']], zoom_start=4)

            # Plot airports on the map
            for index, airport in coordinates_df.iterrows():
                if airport['airport_code'] in airport_codes:
                    folium.Marker(
                        location=[airport['latitude'], airport['longitude']],
                        icon=folium.Icon(color='cadetblue', icon='plane'),
                        tooltip=airport['airport_code'], 
                    ).add_to(map)

                    # Add airport codes as labels
                    folium.Marker(
                        location=[airport['latitude'], airport['longitude']],
                        icon=folium.DivIcon(
                            icon_size=(6, 6),
                            icon_anchor=(2, 2),
                            html=f'<div style="font-size: 15px; font-weight: bold;">{airport["airport_code"]}</div>',
                        ),
                    ).add_to(map)

            # Draw lines connecting the airports along the route
            polyline = folium.PolyLine(locations=coordinates[['latitude', 'longitude']], color='red')
            polyline.add_to(map)

            # Display the map
            folium_static(map)
        
            
    elif option == "Origin":
        with sel_col:
            # slider for leg_sequence
            st.write("##")

            # drop down for airline code
            airport_code_data = pd.DataFrame(coordinates['airport_code'].unique())
            airport_code_data = airport_code_data.sort_values(0, ascending=True)

            airport_code_inp = sel_col.selectbox("Origin airport code: ", options=airport_code_data)


        with disp_col:
            
            st.write("##")
            # Load the CSV files
            coordinates_df = pd.read_csv('coordinates.csv',low_memory=False)
            traffic_df = pd.read_csv('traffic_control.csv',low_memory=False)

            ## Take user inputs
            airport_codes = airport_code_inp
            
            # Filter data based on user inputs
            filtered_df2 = traffic_df[(traffic_df['seg_origin'] == airport_codes)]

            # Check if there are any matching routes
            if filtered_df2.empty:
                st.warning("No routes found originating from this airport")
                exit()  
            
            st.subheader("Selected Routes")
            st.dataframe(filtered_df2)

            st.write("##")

            st.subheader("Visualization")
            st.markdown("The flight routes and airports on the map:")

            my_map = folium.Map(zoom_start= 4)
            
            # Set the maximum number of airports to plot
            max_airports = 5000

            # Initialize counter
            num_airports = 0

            # Iterate through filtered_df2 to plot routes
            for index, row in filtered_df2.iterrows():
                
                if num_airports >= max_airports:
                    break
                
                routing = row['routing']
                airport_codes = routing.split('-')

                # Get coordinates for each airport code
                coordinates = coordinates_df[coordinates_df['airport_code'].isin(airport_codes)][['latitude', 'longitude', 'airport_code']]

                # Plot airports on the map
                for index, airport in coordinates.iterrows():
                    folium.Marker(
                        location=[airport['latitude'], airport['longitude']],
                        icon=folium.Icon(color='red', icon='plane') if airport['airport_code'] == airport_code_inp else folium.Icon(color='cadetblue', icon='plane'),
                        tooltip=airport['airport_code'], 
                    ).add_to(my_map)

                    # Add airport codes as labels
                    if airport['airport_code'] == airport_code_inp:
                        folium.Marker(
                            location=[airport['latitude'], airport['longitude']],
                            icon=folium.DivIcon(
                                icon_size=(6, 6),
                                icon_anchor=(2, 2),
                                html=f'<div style="font-size: 15px; font-weight: bold;">{airport["airport_code"]}</div>',
                            ),
                        ).add_to(my_map)

                    # Draw lines connecting the airports along the route
                    polyline = folium.PolyLine(locations=coordinates[['latitude', 'longitude']].values.tolist(), color='red' )
                    polyline.add_to(my_map)
                    
                    num_airports += 1

            # Display the map
            folium_static(my_map)








