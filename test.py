glue_job_name="predict-elt-dev-postgres-to-snowflake-sync"
env_terms = ["release", "dev", "prod"]
env = next((term for term in env_terms if term in glue_job_name), None)
print(env)