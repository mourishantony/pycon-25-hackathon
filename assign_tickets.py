import json
from collections import defaultdict

def extract_ticket_tags(ticket):
    # Heuristic: Extract keywords from title for skill matching (split by non-alphabetic chars, uppercase/lowercase normalization, underscores)
    words = ticket['title'].replace("-", " ").replace("_", " ").replace("(", " ").replace(")", " ").split()
    tags = set(w.strip(".,:;!?").replace("/", "_") for w in words if len(w) > 2)
    return set(t.title().replace(" ", "_") for t in tags)

def agent_available(agent):
    return agent.get("availability_status", "").lower() == "available"

def ticket_priority(ticket):
    # Higher timestamp => newer, so we want older tickets first
    return ticket.get("creation_timestamp", 0)

def match_score(agent, ticket_tags):
    # Skill overlap: sum(level) of matching skills
    score = 0
    matched = []
    for tag in ticket_tags:
        if tag in agent["skills"]:
            score += agent["skills"][tag] * 3  # skill proficiency
            matched.append(tag)
    # General experience bonus
    score += agent.get("experience_level", 0)
    # Lower current load preferred
    score -= agent.get("current_load", 0) * 2
    return score, matched

def assign_tickets(agents, tickets):
    result = []
    agent_load = {a["agent_id"]: a.get("current_load", 0) for a in agents}
    for ticket in sorted(tickets, key=lambda t: ticket_priority(t)):
        tags = extract_ticket_tags(ticket)
        best_score = float("-inf")
        best_agent = None
        best_matched = []
        for agent in agents:
            if not agent_available(agent):
                continue
            score, matched = match_score(agent, tags)
            # Slight penalty for higher load to balance
            score -= agent_load[agent["agent_id"]]
            if score > best_score:
                best_score = score
                best_agent = agent
                best_matched = matched
        if best_agent:
            agent_load[best_agent["agent_id"]] += 1
            rationale = (
                f"Matched skills: {', '.join(best_matched) if best_matched else 'None'}; "
                f"Agent experience: {best_agent.get('experience_level',0)}; "
                f"Current load after assignment: {agent_load[best_agent['agent_id']]}"
            )
            result.append({
                "ticket_id": ticket["ticket_id"],
                "assigned_agent_id": best_agent["agent_id"],
                "rationale": rationale
            })
        else:
            result.append({
                "ticket_id": ticket["ticket_id"],
                "assigned_agent_id": None,
                "rationale": "No available agent"
            })
    return result

if __name__ == "__main__":
    with open("dataset.json", "r") as f:
        data = json.load(f)
    agents = data["agents"]
    tickets = data["tickets"]
    output = assign_tickets(agents, tickets)
    with open("output_result.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Assigned {len(output)} tickets. Results in output_result.json.")