original_string = "predict_etl_prod_fetch_replication_list"
env_terms = ["release", "dev", "prod"]
env = next((term for term in env_terms if term in original_string), None)
print(f"The current env is {env} ")