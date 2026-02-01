import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  FlatList,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

type SearchResult = {
  id: number;
  barcode?: string;
  name?: string;
  brand_name?: string;
  brand_id?: number;
  category?: string;
  parent_company?: string;
};

export default function SearchScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'brand' | 'product'>('brand');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const endpoint =
        searchType === 'brand'
          ? '/api/search/brands'
          : '/api/search/products';
      const response = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}${endpoint}?q=${searchQuery}`
      );
      setResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleResultPress = async (item: SearchResult) => {
    if (searchType === 'brand') {
      router.push({
        pathname: '/brand-detail',
        params: { brandId: item.id.toString() },
      });
    } else {
      try {
        const response = await axios.get(
          `${EXPO_PUBLIC_BACKEND_URL}/api/product/barcode/${item.barcode}`
        );
        router.push({
          pathname: '/product-detail',
          params: { productData: JSON.stringify(response.data) },
        });
      } catch (error) {
        console.error('Error fetching product:', error);
      }
    }
  };

  const renderItem = ({ item }: { item: SearchResult }) => (
    <TouchableOpacity
      style={styles.resultItem}
      onPress={() => handleResultPress(item)}
    >
      <View style={styles.resultIcon}>
        <Ionicons
          name={searchType === 'brand' ? 'business' : 'cube'}
          size={24}
          color="#FF9933"
        />
      </View>
      <View style={styles.resultContent}>
        <Text style={styles.resultTitle}>
          {searchType === 'brand' ? item.brand_name : item.name}
        </Text>
        {searchType === 'brand' && item.parent_company && (
          <Text style={styles.resultSubtitle}>{item.parent_company}</Text>
        )}
        {searchType === 'product' && item.brand_name && (
          <Text style={styles.resultSubtitle}>{item.brand_name}</Text>
        )}
      </View>
      <Ionicons name="chevron-forward" size={20} color="#fff" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Search</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Search Type Toggle */}
        <View style={styles.toggleContainer}>
          <TouchableOpacity
            style={[
              styles.toggleButton,
              searchType === 'brand' && styles.toggleButtonActive,
            ]}
            onPress={() => {
              setSearchType('brand');
              setResults([]);
            }}
          >
            <Text
              style={[
                styles.toggleText,
                searchType === 'brand' && styles.toggleTextActive,
              ]}
            >
              Brands
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.toggleButton,
              searchType === 'product' && styles.toggleButtonActive,
            ]}
            onPress={() => {
              setSearchType('product');
              setResults([]);
            }}
          >
            <Text
              style={[
                styles.toggleText,
                searchType === 'product' && styles.toggleTextActive,
              ]}
            >
              Products
            </Text>
          </TouchableOpacity>
        </View>

        {/* Search Input */}
        <View style={styles.searchContainer}>
          <Ionicons
            name="search"
            size={20}
            color="#999"
            style={styles.searchIcon}
          />
          <TextInput
            style={styles.searchInput}
            placeholder={`Search ${searchType}s...`}
            placeholderTextColor="#999"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => {
              setSearchQuery('');
              setResults([]);
            }}>
              <Ionicons name="close-circle" size={20} color="#999" />
            </TouchableOpacity>
          )}
        </View>

        <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
          <Text style={styles.searchButtonText}>Search</Text>
        </TouchableOpacity>

        {/* Results */}
        <View style={styles.resultsContainer}>
          {loading ? (
            <ActivityIndicator
              size="large"
              color="#FF9933"
              style={{ marginTop: 40 }}
            />
          ) : results.length > 0 ? (
            <FlatList
              data={results}
              renderItem={renderItem}
              keyExtractor={(item) => item.id.toString()}
              contentContainerStyle={styles.resultsList}
            />
          ) : searchQuery && !loading ? (
            <View style={styles.emptyState}>
              <Ionicons name="search-outline" size={64} color="#666" />
              <Text style={styles.emptyText}>No results found</Text>
              <Text style={styles.emptySubtext}>
                Try searching for popular brands like Amul, Parle, or Nestle
              </Text>
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Ionicons name="information-circle-outline" size={64} color="#666" />
              <Text style={styles.emptyText}>Start Searching</Text>
              <Text style={styles.emptySubtext}>
                Search for FMCG brands or products to see their India Interest Score
              </Text>
            </View>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#16213e',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  toggleContainer: {
    flexDirection: 'row',
    margin: 16,
    backgroundColor: '#16213e',
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  toggleButtonActive: {
    backgroundColor: '#FF9933',
  },
  toggleText: {
    color: '#999',
    fontSize: 16,
    fontWeight: '600',
  },
  toggleTextActive: {
    color: '#fff',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#16213e',
    marginHorizontal: 16,
    marginBottom: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    height: 50,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
  },
  searchButton: {
    backgroundColor: '#FF9933',
    marginHorizontal: 16,
    marginBottom: 16,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  resultsContainer: {
    flex: 1,
  },
  resultsList: {
    padding: 16,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#16213e',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  resultIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  resultContent: {
    flex: 1,
  },
  resultTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  resultSubtitle: {
    color: '#999',
    fontSize: 14,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    color: '#999',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});
