from datetime import datetime
from collections import Counter

def occupancy_frequency(records):
    count = 0
    prev = 0
    for r in records:
        if prev == 0 and r.get("occupied", 0) == 1:
            count += 1
        prev = r.get("occupied", 0)
    return count

def fan_usage_time(records):
    total = 0
    last_on = None

    for r in records:
        ts = datetime.fromisoformat(r["timestamp"])
        if r.get("fan", 0) == 1 and last_on is None:
            last_on = ts
        elif r.get("fan", 0) == 0 and last_on:
            total += (ts - last_on).seconds
            last_on = None

    return total

def led_usage_time(records):
    total = 0
    last_on = None

    for r in records:
        ts = datetime.fromisoformat(r["timestamp"])
        if r.get("led", 0) == 1 and last_on is None:
            last_on = ts
        elif r.get("led", 0) == 0 and last_on:
            total += (ts - last_on).seconds
            last_on = None

    return total

def occupancy_duration(records):
    """Calculate total occupancy duration and categorize visits"""
    durations = []
    last_on = None
    
    for r in records:
        ts = datetime.fromisoformat(r["timestamp"])
        if r.get("occupied", 0) == 1 and last_on is None:
            last_on = ts
        elif r.get("occupied", 0) == 0 and last_on:
            duration_seconds = (ts - last_on).seconds
            durations.append(duration_seconds)
            last_on = None
    
    if not durations:
        return {"total_seconds": 0, "short_visits": 0, "long_stays": 0, "durations": []}
    
    total = sum(durations)
    short_visits = len([d for d in durations if d < 300])  # < 5 min
    long_stays = len([d for d in durations if d > 1800])   # > 30 min
    
    return {
        "total_seconds": total,
        "short_visits": short_visits,
        "long_stays": long_stays,
        "durations": durations
    }

def manual_override_stats(events):
    """Count manual vs automatic events"""
    manual_led = 0
    manual_fan = 0
    auto_on_count = 0
    auto_off_count = 0
    
    for e in events:
        event_type = e.get("event", "")
        if event_type == "MANUAL_LED":
            manual_led += 1
        elif event_type == "MANUAL_FAN":
            manual_fan += 1
        elif event_type == "AUTO_ON":
            auto_on_count += 1
        elif event_type == "AUTO_OFF":
            auto_off_count += 1
    
    return {
        "manual_led": manual_led,
        "manual_fan": manual_fan,
        "manual_total": manual_led + manual_fan,
        "auto_on": auto_on_count,
        "auto_off": auto_off_count,
        "total_auto": auto_on_count + auto_off_count
    }

def peak_usage_time(records):
    """Find peak usage hours"""
    hours = []
    prev = 0
    
    for r in records:
        if prev == 0 and r.get("occupied", 0) == 1:
            ts = datetime.fromisoformat(r["timestamp"])
            hours.append(ts.hour)
        prev = r.get("occupied", 0)
    
    return Counter(hours)

def automation_efficiency(records):
    """Calculate % of time system runs in auto mode vs manual override"""
    auto_mode = 0
    manual_mode = 0
    
    for r in records:
        # If either fan_override or led_override is active, count as manual mode
        if r.get("fan_override", 0) == 1 or r.get("led_override", 0) == 1:
            manual_mode += 1
        else:
            auto_mode += 1
    
    total = auto_mode + manual_mode
    auto_percentage = (auto_mode / total * 100) if total > 0 else 0
    
    return {
        "auto_pct": auto_percentage,
        "auto_count": auto_mode,
        "manual_count": manual_mode
    }

def system_response_time(records):
    """Calculate average response time between occupancy change and device state change"""
    response_times = []
    
    for i in range(1, len(records)):
        prev = records[i-1]
        curr = records[i]
        
        # Detect occupancy change
        if prev.get("occupied", 0) != curr.get("occupied", 0):
            prev_time = datetime.fromisoformat(prev["timestamp"])
            curr_time = datetime.fromisoformat(curr["timestamp"])
            
            # Check if fan/led state changed in response
            if (prev.get("fan", 0) != curr.get("fan", 0) or 
                prev.get("led", 0) != curr.get("led", 0)):
                response_sec = (curr_time - prev_time).total_seconds()
                if response_sec < 60:  # Only count reasonable response times (< 1 min)
                    response_times.append(response_sec)
    
    avg_response = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        "avg_seconds": avg_response,
        "count": len(response_times)
    }
