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

sprDict = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 4,
    7: 5,
    8: 5,
    9: 6,
    10: 6,
    11: 6,
    12: 6,
    13: 7,
    14: 7,
    15: 7,
    16: 7,
    17: 8,
    18: 8,
    19: 8,
    20: 8,
    21: 8,
    22: 8,
    23: 8,
    24: 8,
    25: 9,
    26: 9,
    27: 9,
    28: 9,
    29: 9,
    30: 9,
    31: 9,
    32: 9
}

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

def calcSPR(seedNum):
    if seedNum in sprDict:
        return sprDict[seedNum]
    else:
        return seedNum

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

def calcUF(winnerSeed, loserSeed):
  winnerSpr = calcSPR(winnerSeed)
  loserSpr = calcSPR(loserSeed)

  UF = winnerSpr - loserSpr
  return(UF)

for setId, setInfo in combinedData.items():
  if setInfo['winner']:
    winnerSeed = setInfo['winner']['seedNum']
    for slot in setInfo['slots']:
        if slot['entrantId'] != setInfo['winner']['entrantId']:
            loserSeed = slot['seedNum']
            UF = calcUF(winnerSeed, loserSeed)
            if winnerSeed > loserSeed:
                print(f"{setInfo['winner']['entrantName']} (Seed {winnerSeed}) {setInfo['winner']['stats']['score']['value']} - {setInfo['loser']['stats']['score']['value']} {setInfo['loser']['entrantName']} (Seed {loserSeed}). Upset Facor: {UF}")
                break