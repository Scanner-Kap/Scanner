import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

type Brand = {
  id: number;
  brand_name: string;
  parent_company: string;
  ownership_country: string;
  is_indian_company: boolean;
  manufactures_in_india: string;
  manufacturing_states: string[];
  employees_in_india_estimate: string;
  data_storage_country: string;
};

type Product = {
  id: number;
  barcode: string;
  name: string;
  brand_id: number;
  category: string;
  brand: Brand;
};

type ScoreData = {
  score: number;
  breakdown: any;
  recommendation: string;
};

export default function ProductDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [scoreData, setScoreData] = useState<ScoreData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.productData) {
      const productData = JSON.parse(params.productData as string);
      setProduct(productData);
      fetchScore(productData.brand_id);
    }
  }, [params]);

  const fetchScore = async (brandId: number) => {
    try {
      const response = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}/api/score/${brandId}`
      );
      setScoreData(response.data);
    } catch (error) {
      console.error('Error fetching score:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return '#138808';
    if (score >= 6) return '#4CAF50';
    if (score >= 4) return '#FFC107';
    return '#F44336';
  };

  if (loading || !product) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#FF9933" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Product Details</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Product Info */}
        <View style={styles.section}>
          <Text style={styles.productName}>{product.name}</Text>
          <Text style={styles.brandName}>{product.brand.brand_name}</Text>
          <Text style={styles.category}>{product.category}</Text>
          <Text style={styles.barcode}>Barcode: {product.barcode}</Text>
        </View>

        {/* India Interest Score */}
        {scoreData && (
          <>
            <View style={[styles.section, styles.scoreSection]}>
              <Text style={styles.sectionTitle}>India Interest Score</Text>
              <View style={styles.scoreContainer}>
                <View
                  style={[
                    styles.scoreCircle,
                    { borderColor: getScoreColor(scoreData.score) },
                  ]}
                >
                  <Text
                    style={[
                      styles.scoreText,
                      { color: getScoreColor(scoreData.score) },
                    ]}
                  >
                    {scoreData.score}
                  </Text>
                  <Text style={styles.scoreMax}>/ 10</Text>
                </View>
              </View>
              <Text style={styles.recommendation}>
                {scoreData.recommendation}
              </Text>
            </View>

            {/* Score Breakdown */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Score Breakdown</Text>
              {Object.entries(scoreData.breakdown).map(([key, value]: [string, any]) => (
                <View key={key} style={styles.breakdownItem}>
                  <View style={styles.breakdownHeader}>
                    <Text style={styles.breakdownTitle}>
                      {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </Text>
                    <Text style={styles.breakdownPoints}>
                      {value.points}/{value.max}
                    </Text>
                  </View>
                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${(value.points / value.max) * 100}%`,
                          backgroundColor: getScoreColor((value.points / value.max) * 10),
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.breakdownStatus}>{value.status}</Text>
                </View>
              ))}
            </View>
          </>
        )}

        {/* Brand Intelligence */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Brand Intelligence</Text>
          
          <View style={styles.infoRow}>
            <Ionicons name="business" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Parent Company</Text>
              <Text style={styles.infoValue}>{product.brand.parent_company}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="flag" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Ownership Country</Text>
              <Text style={styles.infoValue}>{product.brand.ownership_country}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="location" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Manufacturing in India</Text>
              <Text style={styles.infoValue}>
                {product.brand.manufactures_in_india === 'true'
                  ? 'Yes (Full)'
                  : product.brand.manufactures_in_india === 'partial'
                  ? 'Partial'
                  : 'No'}
              </Text>
            </View>
          </View>

          {product.brand.manufacturing_states.length > 0 && (
            <View style={styles.infoRow}>
              <Ionicons name="map" size={20} color="#FF9933" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Manufacturing States</Text>
                <Text style={styles.infoValue}>
                  {product.brand.manufacturing_states.join(', ')}
                </Text>
              </View>
            </View>
          )}

          <View style={styles.infoRow}>
            <Ionicons name="people" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Employees in India</Text>
              <Text style={styles.infoValue}>
                {product.brand.employees_in_india_estimate}
              </Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="shield-checkmark" size={20} color="#FF9933" />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Data Storage</Text>
              <Text style={styles.infoValue}>
                {product.brand.data_storage_country}
              </Text>
            </View>
          </View>
        </View>

        {/* View Brand Details Button */}
        <TouchableOpacity
          style={styles.brandButton}
          onPress={() =>
            router.push({
              pathname: '/brand-detail',
              params: { brandId: product.brand_id.toString() },
            })
          }
        >
          <Text style={styles.brandButtonText}>View Full Brand Details</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </ScrollView>
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
  content: {
    flex: 1,
  },
  section: {
    backgroundColor: '#16213e',
    margin: 16,
    padding: 20,
    borderRadius: 12,
  },
  scoreSection: {
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  productName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  brandName: {
    fontSize: 18,
    color: '#FF9933',
    marginBottom: 8,
  },
  category: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
  },
  barcode: {
    fontSize: 12,
    color: '#666',
  },
  scoreContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  scoreCircle: {
    width: 140,
    height: 140,
    borderRadius: 70,
    borderWidth: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  scoreMax: {
    fontSize: 16,
    color: '#999',
  },
  recommendation: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginTop: 8,
  },
  breakdownItem: {
    marginBottom: 20,
  },
  breakdownHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  breakdownTitle: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  breakdownPoints: {
    fontSize: 14,
    color: '#FF9933',
    fontWeight: 'bold',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#1a1a2e',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
  },
  breakdownStatus: {
    fontSize: 12,
    color: '#999',
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  infoContent: {
    flex: 1,
    marginLeft: 12,
  },
  infoLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 15,
    color: '#fff',
  },
  brandButton: {
    flexDirection: 'row',
    backgroundColor: '#FF9933',
    marginHorizontal: 16,
    marginVertical: 16,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginRight: 8,
  },
});
