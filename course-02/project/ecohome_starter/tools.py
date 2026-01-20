"""
Tools for EcoHome Energy Advisor Agent
"""
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from models.energy import DatabaseManager

# Initialize database manager
db_manager = DatabaseManager()

# TODO: Implement get_weather_forecast tool
@tool
def get_weather_forecast(location: str, days: int = 3) -> Dict[str, Any]:
    """
    Get weather forecast for a specific location and number of days.
    
    Args:
        location (str): Location to get weather for (e.g., "San Francisco, CA")
        days (int): Number of days to forecast (1-7)
    
    Returns:
        Dict[str, Any]: Weather forecast data including temperature, conditions, and solar irradiance
        E.g:
        forecast = {
            "location": ...,
            "forecast_days": ...,
            "current": {
                "temperature_c": ...,
                "condition": random.choice(["sunny", "partly_cloudy", "cloudy"]),
                "humidity": ...,
                "wind_speed": ...
            },
            "hourly": [
                {
                    "hour": ..., # for hour in range(24)
                    "temperature_c": ...,
                    "condition": ...,
                    "solar_irradiance": ...,
                    "humidity": ...,
                    "wind_speed": ...
                },
            ]
        }
    """
    # Limit days to 1-7 range
    days = max(1, min(7, days))

    # Weather conditions with their solar irradiance ranges (W/m²)
    weather_types = {
        "sunny": {"irradiance_range": (800, 1000), "weight": 0.4},
        "partly_cloudy": {"irradiance_range": (400, 700), "weight": 0.35},
        "cloudy": {"irradiance_range": (100, 350), "weight": 0.2},
        "rainy": {"irradiance_range": (50, 150), "weight": 0.05}
    }

    # Current weather conditions
    current_condition = random.choices(
        list(weather_types.keys()),
        weights=[w["weight"] for w in weather_types.values()]
    )[0]

    current_temp = random.uniform(15, 28)
    current_humidity = random.randint(40, 80)
    current_wind_speed = random.uniform(5, 25)

    forecast = {
        "location": location,
        "forecast_days": days,
        "current": {
            "temperature_c": round(current_temp, 1),
            "condition": current_condition,
            "humidity": current_humidity,
            "wind_speed": round(current_wind_speed, 1)
        },
        "hourly": [],
        "daily": []
    }

    # Generate hourly forecast for each day
    for day in range(days):
        day_condition = random.choices(
            list(weather_types.keys()),
            weights=[w["weight"] for w in weather_types.values()]
        )[0]

        daily_temps = []
        daily_generation_potential = 0

        for hour in range(24):
            # Temperature varies throughout the day (cooler at night, warmer midday)
            hour_factor = 1 - abs(hour - 14) / 14  # Peak at 2 PM
            base_temp = 12 + random.uniform(-2, 2)  # Night base
            temp_range = 15  # Day-night difference
            temp = base_temp + (temp_range * hour_factor)
            daily_temps.append(temp)

            # Determine hourly condition (mostly consistent with daily condition)
            if random.random() < 0.8:  # 80% chance to match daily condition
                hourly_condition = day_condition
            else:
                hourly_condition = random.choice(list(weather_types.keys()))

            # Solar irradiance - only during daylight hours (6 AM to 8 PM)
            if 6 <= hour <= 20:
                # Peak solar at noon
                solar_factor = max(0, 1 - abs(hour - 13) / 7)
                irr_range = weather_types[hourly_condition]["irradiance_range"]
                base_irradiance = random.uniform(irr_range[0], irr_range[1])
                solar_irradiance = round(base_irradiance * solar_factor, 1)
                daily_generation_potential += solar_irradiance / 1000  # kWh estimate
            else:
                solar_irradiance = 0

            forecast["hourly"].append({
                "day": day,
                "hour": hour,
                "temperature_c": round(temp, 1),
                "condition": hourly_condition,
                "solar_irradiance": solar_irradiance,
                "humidity": random.randint(35, 85),
                "wind_speed": round(random.uniform(3, 20), 1)
            })

        # Daily summary
        forecast["daily"].append({
            "day": day,
            "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
            "condition": day_condition,
            "high_temp_c": round(max(daily_temps), 1),
            "low_temp_c": round(min(daily_temps), 1),
            "solar_generation_potential_kwh": round(daily_generation_potential, 2)
        })

    return forecast

# TODO: Implement get_electricity_prices tool
@tool
def get_electricity_prices(date: str = None) -> Dict[str, Any]:
    """
    Get electricity prices for a specific date or current day.
    
    Args:
        date (str): Date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Dict[str, Any]: Electricity pricing data with hourly rates 
        E.g: 
        prices = {
            "date": ...,
            "pricing_type": "time_of_use",
            "currency": "USD",
            "unit": "per_kWh",
            "hourly_rates": [
                {
                    "hour": .., # for hour in range(24)
                    "rate": ..,
                    "period": ..,
                    "demand_charge": ...
                }
            ]
        }
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Base prices per kWh for different periods (typical California TOU rates)
    pricing_tiers = {
        "off_peak": {"rate": 0.10, "hours": list(range(0, 6)) + list(range(23, 24))},  # 11 PM - 6 AM
        "partial_peak": {"rate": 0.15, "hours": list(range(6, 16)) + list(range(21, 23))},  # 6 AM - 4 PM, 9 PM - 11 PM
        "peak": {"rate": 0.25, "hours": list(range(16, 21))}  # 4 PM - 9 PM
    }

    prices = {
        "date": date,
        "pricing_type": "time_of_use",
        "currency": "USD",
        "unit": "per_kWh",
        "hourly_rates": [],
        "summary": {
            "off_peak_rate": 0.10,
            "partial_peak_rate": 0.15,
            "peak_rate": 0.25,
            "off_peak_hours": "11 PM - 6 AM",
            "partial_peak_hours": "6 AM - 4 PM, 9 PM - 11 PM",
            "peak_hours": "4 PM - 9 PM"
        }
    }

    for hour in range(24):
        # Determine which period this hour falls into
        period = "partial_peak"  # Default
        rate = 0.15
        demand_charge = 0.0

        for tier_name, tier_info in pricing_tiers.items():
            if hour in tier_info["hours"]:
                period = tier_name
                rate = tier_info["rate"]
                break

        # Add demand charge during peak hours
        if period == "peak":
            demand_charge = 0.05  # Additional demand charge during peak

        # Add slight random variation to simulate real-world fluctuations
        rate_variation = random.uniform(-0.01, 0.01)
        final_rate = round(rate + rate_variation, 3)

        prices["hourly_rates"].append({
            "hour": hour,
            "rate": final_rate,
            "period": period,
            "demand_charge": demand_charge,
            "total_rate": round(final_rate + demand_charge, 3)
        })

    return prices

@tool
def query_energy_usage(start_date: str, end_date: str, device_type: str = None) -> Dict[str, Any]:
    """
    Query energy usage data from the database for a specific date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        device_type (str): Optional device type filter (e.g., "EV", "HVAC", "appliance")
    
    Returns:
        Dict[str, Any]: Energy usage data with consumption details
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        records = db_manager.get_usage_by_date_range(start_dt, end_dt)
        
        if device_type:
            records = [r for r in records if r.device_type == device_type]
        
        usage_data = {
            "start_date": start_date,
            "end_date": end_date,
            "device_type": device_type,
            "total_records": len(records),
            "total_consumption_kwh": round(sum(r.consumption_kwh for r in records), 2),
            "total_cost_usd": round(sum(r.cost_usd or 0 for r in records), 2),
            "records": []
        }
        
        for record in records:
            usage_data["records"].append({
                "timestamp": record.timestamp.isoformat(),
                "consumption_kwh": record.consumption_kwh,
                "device_type": record.device_type,
                "device_name": record.device_name,
                "cost_usd": record.cost_usd
            })
        
        return usage_data
    except Exception as e:
        return {"error": f"Failed to query energy usage: {str(e)}"}

@tool
def query_solar_generation(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Query solar generation data from the database for a specific date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    
    Returns:
        Dict[str, Any]: Solar generation data with production details
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        records = db_manager.get_generation_by_date_range(start_dt, end_dt)
        
        generation_data = {
            "start_date": start_date,
            "end_date": end_date,
            "total_records": len(records),
            "total_generation_kwh": round(sum(r.generation_kwh for r in records), 2),
            "average_daily_generation": round(sum(r.generation_kwh for r in records) / max(1, (end_dt - start_dt).days), 2),
            "records": []
        }
        
        for record in records:
            generation_data["records"].append({
                "timestamp": record.timestamp.isoformat(),
                "generation_kwh": record.generation_kwh,
                "weather_condition": record.weather_condition,
                "temperature_c": record.temperature_c,
                "solar_irradiance": record.solar_irradiance
            })
        
        return generation_data
    except Exception as e:
        return {"error": f"Failed to query solar generation: {str(e)}"}

@tool
def get_recent_energy_summary(hours: int = 24) -> Dict[str, Any]:
    """
    Get a summary of recent energy usage and solar generation.
    
    Args:
        hours (int): Number of hours to look back (default 24)
    
    Returns:
        Dict[str, Any]: Summary of recent energy data
    """
    try:
        usage_records = db_manager.get_recent_usage(hours)
        generation_records = db_manager.get_recent_generation(hours)
        
        summary = {
            "time_period_hours": hours,
            "usage": {
                "total_consumption_kwh": round(sum(r.consumption_kwh for r in usage_records), 2),
                "total_cost_usd": round(sum(r.cost_usd or 0 for r in usage_records), 2),
                "device_breakdown": {}
            },
            "generation": {
                "total_generation_kwh": round(sum(r.generation_kwh for r in generation_records), 2),
                "average_weather": "sunny" if generation_records else "unknown"
            }
        }
        
        # Calculate device breakdown
        for record in usage_records:
            device = record.device_type or "unknown"
            if device not in summary["usage"]["device_breakdown"]:
                summary["usage"]["device_breakdown"][device] = {
                    "consumption_kwh": 0,
                    "cost_usd": 0,
                    "records": 0
                }
            summary["usage"]["device_breakdown"][device]["consumption_kwh"] += record.consumption_kwh
            summary["usage"]["device_breakdown"][device]["cost_usd"] += record.cost_usd or 0
            summary["usage"]["device_breakdown"][device]["records"] += 1
        
        # Round the breakdown values
        for device_data in summary["usage"]["device_breakdown"].values():
            device_data["consumption_kwh"] = round(device_data["consumption_kwh"], 2)
            device_data["cost_usd"] = round(device_data["cost_usd"], 2)
        
        return summary
    except Exception as e:
        return {"error": f"Failed to get recent energy summary: {str(e)}"}

@tool
def search_energy_tips(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search for energy-saving tips and best practices using RAG.
    
    Args:
        query (str): Search query for energy tips
        max_results (int): Maximum number of results to return
    
    Returns:
        Dict[str, Any]: Relevant energy tips and best practices
    """
    try:
        # Initialize vector store if it doesn't exist
        persist_directory = "data/vectorstore"
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # Load documents if vector store doesn't exist
        if not os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
            # Load documents
            documents = []
            for doc_path in ["data/documents/tip_device_best_practices.txt", "data/documents/tip_energy_savings.txt"]:
                if os.path.exists(doc_path):
                    loader = TextLoader(doc_path)
                    docs = loader.load()
                    documents.extend(docs)
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(documents)
            
            # Create vector store
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=persist_directory
            )
        else:
            # Load existing vector store
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
        
        # Search for relevant documents
        docs = vectorstore.similarity_search(query, k=max_results)
        
        results = {
            "query": query,
            "total_results": len(docs),
            "tips": []
        }
        
        for i, doc in enumerate(docs):
            results["tips"].append({
                "rank": i + 1,
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "relevance_score": "high" if i < 2 else "medium" if i < 4 else "low"
            })
        
        return results
    except Exception as e:
        return {"error": f"Failed to search energy tips: {str(e)}"}

@tool
def calculate_energy_savings(device_type: str, current_usage_kwh: float, 
                           optimized_usage_kwh: float, price_per_kwh: float = 0.12) -> Dict[str, Any]:
    """
    Calculate potential energy savings from optimization.
    
    Args:
        device_type (str): Type of device being optimized
        current_usage_kwh (float): Current energy usage in kWh
        optimized_usage_kwh (float): Optimized energy usage in kWh
        price_per_kwh (float): Price per kWh (default 0.12)
    
    Returns:
        Dict[str, Any]: Savings calculation results
    """
    savings_kwh = current_usage_kwh - optimized_usage_kwh
    savings_usd = savings_kwh * price_per_kwh
    savings_percentage = (savings_kwh / current_usage_kwh) * 100 if current_usage_kwh > 0 else 0
    
    return {
        "device_type": device_type,
        "current_usage_kwh": current_usage_kwh,
        "optimized_usage_kwh": optimized_usage_kwh,
        "savings_kwh": round(savings_kwh, 2),
        "savings_usd": round(savings_usd, 2),
        "savings_percentage": round(savings_percentage, 1),
        "price_per_kwh": price_per_kwh,
        "annual_savings_usd": round(savings_usd * 365, 2)
    }


TOOL_KIT = [
    get_weather_forecast,
    get_electricity_prices,
    query_energy_usage,
    query_solar_generation,
    get_recent_energy_summary,
    search_energy_tips,
    calculate_energy_savings
]
