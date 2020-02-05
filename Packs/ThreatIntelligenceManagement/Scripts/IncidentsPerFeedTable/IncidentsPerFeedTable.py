from typing import Any, Dict, Set


def get_incidents_count_by_feed(feed, from_date, query=None) -> int:
    """Counts the incidents amount that fits the query and has indicators that came from the given feed.
        Args:
                feed: Feed from which the incidents' indicator should be from
                from_date: The date from the incidents should be queried
                query: Additional filters for the 'getIncidents' command
        Returns:
            total amount of incidents returned.
    """
    params = generate_query_params(feed, from_date, query)
    res = demisto.executeCommand("getIncidents", params)
    queried_incidents_count = res[0]["Contents"]["total"]
    return queried_incidents_count


def generate_query_params(feed, from_date, query):
    """Generating parameters for 'getIncidents' command according to relevant feed, date, and additional query
        Args:
                feed: Feed from which the incidents indicator should be from
                from_date: The date from the incidents should be queried
                query: Additional filters for the 'getIncidents' command

        Returns:
            A set with feed names
        """
    query_string = f'indicator.sourceBrands:{feed}'
    if query:
        query_string += f' and ({query})'
    params = {"query": query_string}
    if from_date:
        params.update({"fromdate": from_date})
    return params


def get_feeds() -> set:
    """Return all enabled modules
            Returns:
                A set with feed names
    """
    modules = demisto.getModules()  # type: ignore  # pylint: disable=E1101
    return {module_details["brand"] for module_details in modules.values() if  # pylint: disable=E1101
            active_feed(module_details)}


def active_feed(module) -> bool:
    """Checks if module is active and if it's a feed and return a boolean accordingly
        Args:
                module: Module to check if is active feed
        Returns:
            True if the module's brand has 'feed' in it and if module 'state is 'active' else False
    """
    return 'feed' in module["brand"].lower() and module["state"] == 'active'


def generate_table_data(feed_types: Set[str], from_date: str) -> Dict[str, Any]:
    """Generate a table data structure with all number of incidents, false positive incidents, and high priority incidents
        Args:
               from_date: The data from which the data should be queried
               feed_types :A set Containing feed names
        Returns:
            The total number of enabled feeds and the generated data about them.
        """
    data = []
    for feed in feed_types:
        incidents_count_by_feed = get_incidents_count_by_feed(feed, from_date)
        false_positive_incidents_count_by_feed = get_incidents_count_by_feed(feed, from_date,
                                                                             query="closeReason:False Positive")
        high_priority_incidents_count_by_feed = get_incidents_count_by_feed(feed, from_date,
                                                                            query="severity:Critical or severity:High")
        data.append({"Feed name": feed,
                     "Incidents": incidents_count_by_feed,
                     "False Positive Incidents": false_positive_incidents_count_by_feed,
                     "High Priority Incidents": high_priority_incidents_count_by_feed})

    table_data = {"total": len(feed_types), "data": data}
    return table_data


def main():
    feed_types = get_feeds()
    from_date = demisto.args().get('from')
    table_data = generate_table_data(feed_types, from_date)
    human_readable = tableToMarkdown('Incidents count by feed', table_data)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': table_data,
        'ContentsFormat': formats['text'],
        'ReadableContentsFormat': formats['markdown'],
        'HumanReadable': human_readable
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
