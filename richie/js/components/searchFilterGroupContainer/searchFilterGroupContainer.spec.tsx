import { CourseState } from '../../data/course/reducer';
import Organization from '../../types/Organization';
import { mapStateToProps } from './searchFilterGroupContainer';

describe('components/searchFilterGroupContainer', () => {
  it('mapStateToProps returns a FilterDefinition for a hardcoded filter group', () => {
    expect(mapStateToProps({ resources: {} }, { machineName: 'new' }))
    .toEqual({
      filter: {
        humanName: 'New courses',
        machineName: 'status',
        values: [
          { primaryKey: 'new', humanName: 'First session'},
        ],
      },
    });
  });

  it('mapStateToProps builds a filter definition from the facet for a resource-based filter group', () => {
    const state = {
      resources: {
        course: {
          byId: {},
          currentQuery: {
            facets: { organization: { 21: 3, 42: 15, 84: 7 } },
            items: {},
            queryKey: '',
            total_count: 22,
          },
        } as CourseState,
        organization: {
          byId: {
            21: { id: 21, name: 'Organization #Twenty-One' } as Organization,
            42: { id: 42, name: 'Organization #Fourty-Two' } as Organization,
            84: { id: 84, name: 'Organization #Eighty-Four' } as Organization,
          },
        },
      },
    };

    expect(mapStateToProps(state, { machineName: 'organization' }))
    .toEqual({
      filter: {
        humanName: 'Organizations',
        machineName: 'organization',
        values: [
          { count: 15, humanName: 'Organization #Fourty-Two', primaryKey: '42' },
          { count: 7, humanName: 'Organization #Eighty-Four', primaryKey: '84' },
          { count: 3, humanName: 'Organization #Twenty-One', primaryKey: '21' },
        ],
      },
    });
  });

  it('mapStateToProps still builds a default filter group when missing a resource-related facet', () => {
    const state = {
      resources: {
        organization: {
          byId: {
            21: { id: 21, name: 'Organization #Twenty-One' } as Organization,
            42: { id: 42, name: 'Organization #Fourty-Two' } as Organization,
            84: { id: 84, name: 'Organization #Eighty-Four' } as Organization,
          },
        },
      },
    };

    expect(mapStateToProps(state, { machineName: 'organization' }))
    .toEqual({
      filter: {
        humanName: 'Organizations',
        machineName: 'organization',
        values: [
          { humanName: 'Organization #Twenty-One', primaryKey: '21' },
          { humanName: 'Organization #Fourty-Two', primaryKey: '42' },
          { humanName: 'Organization #Eighty-Four', primaryKey: '84' },
        ],
      },
    });
  });
});