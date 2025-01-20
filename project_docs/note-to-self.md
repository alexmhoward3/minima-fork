## startup 
docker-compose -f docker-compose-mcp.yml up --build -d

## stop
docker-compose -f docker-compose-mcp.yml down

## both
docker-compose -f docker-compose-mcp.yml down; docker-compose -f docker-compose-mcp.yml up --build -d

## clear cache
docker volume rm minima-fork_huggingface_cache

## system prune
docker system prune -a

## Next
It looks like it's processing txt files and pdfs, but need to get it to process markdown files