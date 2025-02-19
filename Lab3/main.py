from dotenv import load_dotenv
from graphqlclient import GraphQLClient
import json
import os

load_dotenv()
authToken = os.getenv('API_KEY')
if not authToken:
    raise ValueError('API_KEY environment variable not set')
apiVersion = 'alpha'

phaseId = 1886788
perPage = 100
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

getSeedsResult = client.execute('''
query PhaseSeeds($phaseId: ID!, $page: Int!, $perPage: Int!) {
  phase(id:$phaseId) {
    id
    seeds(query: {
      page: $page
      perPage: $perPage
    }) {
      pageInfo {
        total
        totalPages
      }
      nodes {
        id
        seedNum
        entrant {
          id
          participants {
            id
            gamerTag
          }
        }
      }
    }
    sets(
      page: $page
      perPage: $perPage
      sortType: STANDARD
    ) {
      pageInfo {
        total
      }
      nodes {
        id
        slots {
          id
          entrant {
            id
            name
          }
          standing {
            placement
            stats {
              score {
                label
                value
              }
            }
          }
        }
      }
    }
  }
}
''', {
    "phaseId": phaseId,
    "page": 1,
    "perPage": perPage
})

resData = json.loads(getSeedsResult)

if 'errors' in resData:
    print('Error:')
    print(resData['errors'])
elif not resData['data']['phase']:
    print('Phase not found')
else:
    seedings = resData['data']['phase']['seeds']['nodes']
    sets = resData['data']['phase']['sets']['nodes']
    
    seedsDict = {seed['entrant']['id']: seed for seed in seedings}

    combinedData = {}
    for set in sets:
        setId = set['id']
        combinedData[setId] = {
            'setId': setId,
            'slots': []
        }
        setWinner = None
        for slot in set['slots']:
            entrant = slot['entrant']
            if entrant:
                entrantId = entrant['id']
                seedInfo = seedsDict.get(entrantId, {})
                slotData = {
                    'entrantId': entrantId,
                    'entrantName': entrant['name'],
                    'seedNum': seedInfo.get('seedNum', 'N/A'),
                    'gamerTag': seedInfo.get('entrant', {}).get('participants', [{}])[0].get('gamerTag', 'N/A'),
                    'placement': slot['standing']['placement'] if slot['standing'] else 'N/A',
                    'stats': slot['standing']['stats']
                }
                combinedData[setId]['slots'].append(slotData)
                if slot['standing'] and slot['standing']['placement'] == 1:
                    setWinner = slotData
                elif slot['standing'] and slot['standing']['placement'] == 2:
                    setLoser = slotData
        combinedData[setId]['winner'] = setWinner
        combinedData[setId]['loser'] = setLoser

    for setId, setInfo in combinedData.items():
        if setInfo['winner']:
            winnerSeed = setInfo['winner']['seedNum']
            for slot in setInfo['slots']:
                if slot['entrantId'] != setInfo['winner']['entrantId']:
                    loserSeed = slot['seedNum']
                    if winnerSeed > loserSeed:
                        print(f"{setInfo['winner']['entrantName']} (Seed {winnerSeed}) {setInfo['winner']['stats']['score']['value']} - {setInfo['loser']['stats']['score']['value']} {setInfo['loser']['entrantName']} (Seed {loserSeed})")
                        break