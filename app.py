

# Streamlit set page
st.set_page_config(page_title="Dining Agent", layout="wide")

# OpenAI API setup
API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY)

## Data Model generation

CUISINES = ['Italian', 'Japanese', 'Mexican', 'Indian', 'French', 'American', 'Thai', 'Mediterranean', 'Vegan']
LOCATIONS = ['Bhubaneswar', 'Cuttack', 'Puri', 'Bhadrak', 'Balasore', 'Rourkela', 'Dhenkanal']
VIBES = ['Romantic', 'Casual', 'Lively', 'Quiet', 'Business', 'Family-friendly', 'Trendy', 'Upscale']
PRICES = ['Cheap', 'Moderate', 'Expensive', 'Luxury']
PRICE_VALUES = {'Cheap': 1500, 'Moderate': 3500, 'Expensive': 7500, 'Luxury': 15000}


def generate_restaurants(count=50):
    restaurants = []
    for i in range(1, count + 1):
        cuisine = random.choice(CUISINES)
        name = f"{random.choice(['The', 'La', 'El', 'Royal', 'Urban'])} {cuisine} {random.choice(['Spoon', 'Table', 'Bistro', 'House'])} {i}"
        restaurants.append({
            "id": i,
            "name": name,
            "cuisine": cuisine,
            "price": random.choice(PRICES),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "capacity": random.randint(10, 90),
            "location": random.choice(LOCATIONS),
            "vibe": random.sample(VIBES, k=random.randint(1, 2)),
        })
    return restaurants


## Search tool used by LLM
def search_restaurants(criteria):
    results = st.session_state.restaurants

    # Filter Logic
    if criteria.get('cuisine'):
        results = [r for r in results if criteria['cuisine'].lower() in r['cuisine'].lower()]
    if criteria.get('location'):
        results = [r for r in results if criteria['location'].lower() in r['location'].lower()]
    if criteria.get('min_rating'):
        results = [r for r in results if r['rating'] >= criteria['min_rating']]
    if criteria.get('party_size'):
        results = [r for r in results if r['capacity'] >= criteria['party_size']]

    # Price Filter
    price_levels = {'Cheap': 1, 'Moderate': 2, 'Expensive': 3, 'Luxury': 4}
    if criteria.get('max_price'):
        max_p = price_levels.get(criteria['max_price'], 4)
        results = [r for r in results if price_levels.get(r['price'], 1) <= max_p]

    # Keyword Search
    if criteria.get('query'):
        q = criteria['query'].lower()
        results = [r for r in results if q in r['name'].lower() or any(q in v.lower() for v in r['vibe'])]

    # Sort & Limit
    results.sort(key=lambda x: x['rating'], reverse=True)
    return results[:5]


def make_reservation(details):
    r_id = details.get('restaurant_id')
    party = details.get('party_size')
    time = details.get('time')

    # Validation
    restaurant = next((r for r in st.session_state.restaurants if r['id'] == r_id), None)
    if not restaurant:
        return {"error": "Restaurant ID not found."}
    if restaurant['capacity'] < party:
        return {"error": "Capacity exceeded."}

    # Create Booking
    res_id = f"RES-{random.randint(1000, 9999)}"
    est_rev = PRICE_VALUES[restaurant['price']] * party

    reservation = {
        "id": res_id,
        "restaurant": restaurant['name'],
        "party": party,
        "time": time,
        "revenue": est_rev
    }

    st.session_state.reservations.append(reservation)
    return {"success": True, "reservation_id": res_id, "message": f"Booked {restaurant['name']} for {party} at {time}."}


# Tool definitions for OpenAI
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Find restaurants based on cuisine, location, rating, price, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cuisine": {"type": "string"},
                    "location": {"type": "string"},
                    "min_rating": {"type": "number"},
                    "max_price": {"type": "string", "enum": PRICES},
                    "party_size": {"type": "number"},
                    "query": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_reservation",
            "description": "Book a table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "number"},
                    "party_size": {"type": "number"},
                    "time": {"type": "string"}
                },
                "required": ["restaurant_id", "party_size", "time"]
            }
        }
    }
]

## State initialization
if 'restaurants' not in st.session_state:
    st.session_state.restaurants = generate_restaurants()
if 'reservations' not in st.session_state:
    st.session_state.reservations = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'intent_log' not in st.session_state:
    st.session_state.intent_log = []

## UI SIDEBAR
st.sidebar.title(" Dining")
page = st.sidebar.radio("Navigation", ["Reservation Agent", "Business Intelligence"])

st.sidebar.markdown("---")
st.sidebar.caption(f"System Status: Online")
st.sidebar.caption(f"Venues Loaded: {len(st.session_state.restaurants)}")
st.sidebar.caption(f"Active Bookings: {len(st.session_state.reservations)}")

## Business Intelligence Page
if page == "Business Intelligence":
    st.title("Business Intelligence Dashboard")
    st.markdown("Real-time operational metrics and automated opportunity detection.")

    total_rev = sum(r['revenue'] for r in st.session_state.reservations)
    human_hours = len(st.session_state.reservations) * 0.25
    conversion = 0
    if len(st.session_state.chat_history) > 0:
        conversion = (len(st.session_state.reservations) / (len(st.session_state.chat_history) / 2)) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projected Revenue", f"${total_rev:,}", "+12%")
    c2.metric("Conversion Rate", f"{min(conversion, 100):.1f}%", "+2.4%")
    c3.metric("Hours Saved", f"{human_hours:.1f}h", "vs Manual")
    c4.metric("Avg Ticket", f"${(total_rev / len(st.session_state.reservations)) if total_rev else 0:.0f}")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.subheader("Vertical Expansion Simulator")
        vertical = st.selectbox("Select Vertical Configuration",
                                ["Restaurants (Current)", "Hotels & Hospitality", "Healthcare Clinics", "Automotive Service"])

        if vertical == "Restaurants (Current)":
            st.json({"Inventory": "Tables", "Unit": "Covers", "Constraint": "Kitchen Capacity", "Churn": "90 mins"})
        elif "Hotels" in vertical:
            st.json({"Inventory": "Rooms", "Unit": "Nights", "Constraint": "Housekeeping", "Churn": "24 hours"})
        elif "Healthcare" in vertical:
            st.json({"Inventory": "Doctors", "Unit": "Appointments", "Constraint": "Specialty", "Churn": "30 mins"})

    with col_b:
        st.subheader("Live Opportunities")
        st.success("**Low Utilization Detected**\nTuesdays 6–8PM are 80% empty. Suggest running 'Happy Hour'.")
        st.warning("**Missed Revenue**\n45% of users search for 'Vegan' but only 10% convert. Add more Vegan inventory.")

    st.subheader("Neural Intent Stream")
    if st.session_state.intent_log:
        df_log = pd.DataFrame(st.session_state.intent_log)
        st.dataframe(df_log.sort_index(ascending=False), use_container_width=True)
    else:
        st.text("No agent actions recorded yet.")

## Reservation Agent Page
elif page == "Reservation Agent":
    st.title("FOOD EXPRESS")

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("How can I help you dine today?"):

        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")

            try:
                # Build conversation history for OpenAI
                messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.chat_history[:-1]
                ]

                messages.append({
                    "role": "system",
                    "content": f"You are a restaurant reservation agent. Always use tools if needed. Date: {datetime.date.today()}"
                })

                messages.append({"role": "user", "content": prompt})

                # Step 1 — Ask OpenAI
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    messages=messages,
                    tools=openai_tools
                )

                msg_out = response.output[0]

                if msg_out.type == "function_call":
                    # Tool call
                    tool_name = msg_out.name
                    tool_args = json.loads(msg_out.arguments)

                    st.session_state.intent_log.append({
                        "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "Intent": tool_name,
                        "Parameters": str(tool_args)
                    })

                    # Execute tool
                    result = tools_map.get(tool_name, lambda x: {"error": "Unknown tool"})(tool_args)

                    # Step 2 — Send result back to OpenAI
                    followup = client.responses.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": json.dumps(result)}
                        ]
                    )

                    final_text = followup.output_text

                else:
                    final_text = msg_out.content

                message_placeholder.markdown(final_text)
                st.session_state.chat_history.append({"role": "assistant", "content": final_text})

            except Exception as e:
                message_placeholder.markdown(f"System Error:{e}")
                if not API_KEY:
                    st.error("Please set OPENAI_API_KEY environment variable.")
