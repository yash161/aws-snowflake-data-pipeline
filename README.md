# WS DevOps Automation for Data Migration

This project automates the migration of data from SQL Server to Snowflake, minimizing manual effort and enhancing deployment accuracy.

## Technologies Used
- **Python**: Data extraction and loading  
- **AWS Step Functions**: Workflow orchestration  
- **Terraform**: Infrastructure as Code (IaC) for cloud provisioning  
- **GitLab CI/CD**: Automated error detection and deployment  

## Architecture Overview
1. **Data Extraction**: SQL Server data pulled via Python.  
2. **Data Transfer**: Python scripts push data to Snowflake.  
3. **Workflow Management**: AWS Step Functions automate tasks.  
4. **Infrastructure Setup**: Terraform provisions necessary cloud resources.  
5. **Deployment**: GitLab CI/CD pipeline ensures smooth delivery.  

