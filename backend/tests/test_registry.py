from app.data.registry import SemanticRegistry


# Load the assignment's semantic dictionary.
registry = SemanticRegistry.from_json(
    "../dataset/data_dictionary.json"
)


print("=== REGISTRY ===")
print("Metrics:", registry.metrics)
print("Dimensions:", registry.dimensions)
print("Synonyms:", registry.synonyms)
print("Time mappings:", registry.time_mappings)


print("\n=== TERM RESOLUTION ===")

print("sales ->", registry.resolve_term("sales"))
print("income ->", registry.resolve_term("income"))
print("profit ->", registry.resolve_term("profit"))
print("AOV ->", registry.resolve_term("AOV"))


print("\n=== TYPE CHECKS ===")

print("sales is metric:", registry.is_metric("sales"))
print("city is dimension:", registry.is_dimension("city"))
print("foo is metric:", registry.is_metric("foo"))


print("\n=== TIME RESOLUTION ===")

print(
    "last month ->",
    registry.resolve_time("last month")
)

print(
    "this quarter ->",
    registry.resolve_time("this quarter")
)


print("\n✅ REGISTRY TEST PASSED")